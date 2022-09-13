// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

package main

import (
	"crypto/tls"
	"crypto/x509"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"

	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/buildpipeline"
	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/directory"
	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/exe"
	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/logger"
	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/rpm"
	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/safechroot"
	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/shell"

	"gopkg.in/alecthomas/kingpin.v2"
)

type fileSignaturesWrapper struct {
	FileSignatures map[string]string `json:"Signatures"`
}

const (
	srpmOutDir     = "SRPMS"
	srpmSPECDir    = "SPECS"
	srpmSOURCESDir = "SOURCES"
)

type fileType int

const (
	fileTypePatch  fileType = iota
	fileTypeSource fileType = iota
)

type signatureHandlingType int

const (
	signatureEnforce   signatureHandlingType = iota
	signatureSkipCheck signatureHandlingType = iota
	signatureUpdate    signatureHandlingType = iota
)

const (
	signatureEnforceString   = "enforce"
	signatureSkipCheckString = "skip"
	signatureUpdateString    = "update"
)

const (
	defaultBuildDir    = "./build/SRPMS"
	defaultWorkerCount = "10"
)

// sourceRetrievalConfiguration holds information on where to hydrate files from.
type sourceRetrievalConfiguration struct {
	localSourceDir string
	sourceURL      string
	caCerts        *x509.CertPool
	tlsCerts       []tls.Certificate

	signatureHandling signatureHandlingType
	signatureLookup   map[string]string
}

// packResult holds the worker results from packing a SPEC file into an SRPM.
type packResult struct {
	specFile string
	srpmFile string
	err      error
}

// specState holds the state of a SPEC file: if it should be packed and the resulting SRPM if it is.
type specState struct {
	specFile string
	srpmFile string
	toPack   bool
	err      error
}

var (
	app = kingpin.New("srpmpacker", "A tool to package a SRPM.")

	specsDir = exe.InputDirFlag(app, "Path to the SPEC directory to create SRPMs from.")
	outDir   = exe.OutputDirFlag(app, "Directory to place the output SRPM.")
	logFile  = exe.LogFileFlag(app)
	logLevel = exe.LogLevelFlag(app)

	buildDir = app.Flag("build-dir", "Directory to store temporary files while building.").Default(defaultBuildDir).String()
	distTag  = app.Flag("dist-tag", "The distribution tag SRPMs will be built with.").Required().String()
	runCheck = app.Flag("run-check", "Whether or not to run the spec file's check section during package build.").Bool()

	workers          = app.Flag("workers", "Number of concurrent goroutines to parse with.").Default(defaultWorkerCount).Int()
	nestedSourcesDir = app.Flag("nested-sources", "Set if for a given SPEC, its sources are contained in a SOURCES directory next to the SPEC file.").Bool()

	// Use String() and not ExistingFile() as the Makefile may pass an empty string if the user did not specify any of these options
	sourceURL     = app.Flag("source-url", "URL to a source server to download SPEC sources from.").String()
	caCertFile    = app.Flag("ca-cert", "Root certificate authority to use when downloading files.").String()
	tlsClientCert = app.Flag("tls-cert", "TLS client certificate to use when downloading files.").String()
	tlsClientKey  = app.Flag("tls-key", "TLS client key to use when downloading files.").String()
	specInput     = app.Flag("spec-input", "Spec that needs SRPM.").String()
	srpmURLs      = app.Flag("srpm-urls", "urls for SRPM.").String()

	workerTar = app.Flag("worker-tar", "Full path to worker_chroot.tar.gz. If this argument is empty, SRPMs will be packed in the host environment.").ExistingFile()

	validSignatureLevels = []string{signatureEnforceString, signatureSkipCheckString, signatureUpdateString}
	signatureHandling    = app.Flag("signature-handling", "Specifies how to handle signature mismatches for source files.").Default(signatureEnforceString).PlaceHolder(exe.PlaceHolderize(validSignatureLevels)).Enum(validSignatureLevels...)
)

func main() {
	app.Version(exe.ToolkitVersion)
	kingpin.MustParse(app.Parse(os.Args[1:]))
	logger.InitBestEffort(*logFile, *logLevel)
	logger.Log.Infof("Begin SRPM downloader")
	logger.Log.Infof("SRPM for %s", *specInput)

	if *workers <= 0 {
		logger.Log.Fatalf("Value in --workers must be greater than zero. Found %d", *workers)
	}

	// Create a template configuration that all packed SRPM will be based on.
	var templateSrcConfig sourceRetrievalConfiguration

	switch *signatureHandling {
	case signatureEnforceString:
		templateSrcConfig.signatureHandling = signatureEnforce
	case signatureSkipCheckString:
		logger.Log.Warn("Skipping signature enforcement")
		templateSrcConfig.signatureHandling = signatureSkipCheck
	case signatureUpdateString:
		logger.Log.Warn("Will update signature files as needed")
		templateSrcConfig.signatureHandling = signatureUpdate
	default:
		logger.Log.Fatalf("Invalid signature handling encountered: %s. Allowed: %s", *signatureHandling, validSignatureLevels)
	}

	// Setup remote source configuration
	var err error
	var packageName []string
	templateSrcConfig.sourceURL = *sourceURL
	templateSrcConfig.caCerts, err = x509.SystemCertPool()
	logger.PanicOnError(err, "Received error calling x509.SystemCertPool(). Error: %v", err)
	if *caCertFile != "" {
		newCACert, err := ioutil.ReadFile(*caCertFile)
		if err != nil {
			logger.Log.Panicf("Invalid CA certificate (%s), error: %s", *caCertFile, err)
		}

		templateSrcConfig.caCerts.AppendCertsFromPEM(newCACert)
	}

	if *tlsClientCert != "" && *tlsClientKey != "" {
		cert, err := tls.LoadX509KeyPair(*tlsClientCert, *tlsClientKey)
		if err != nil {
			logger.Log.Panicf("Invalid TLS client key pair (%s) (%s), error: %s", *tlsClientCert, *tlsClientKey, err)
		}

		templateSrcConfig.tlsCerts = append(templateSrcConfig.tlsCerts, cert)
	}

	//spec := "/home/rachel/repos/CBL-Mariner-test/SPECS/iptables/iptables.spec"

	packageName, err = getURLSRPMsWrapper(*specsDir, *distTag, *buildDir, *outDir, *workerTar, *workers, *nestedSourcesDir, *runCheck, *specInput, templateSrcConfig)
	logger.PanicOnError(err)
	srpmfilename := packageName[0]

	// Assumes that srpmURLs come in as ',' seperated
	urls := strings.Split(*srpmURLs, ",")
	// for _, n := range urls {
	// 	logger.Log.Infof("%s", n)
	// }
	for _, url := range urls {
		fullurlwithsrpm := url + "/" + srpmfilename

		wgetArgs := []string{
			fullurlwithsrpm,
		}
		_, stderr, err := shell.Execute("wget", wgetArgs...)
		if err != nil {
			logger.Log.Warn(stderr)
		} else {
			mvArgs := []string{
				srpmfilename,
				*outDir,
			}
			_, stderr, err := shell.Execute("mv", mvArgs...)
			if err != nil {
				logger.Log.Warn(stderr)
			}
			break
		}
	}
}

// createAllSRPMsWrapper wraps createAllSRPMs to conditionally run it inside a chroot.
// If workerTar is non-empty, packing will occur inside a chroot, otherwise it will run on the host system.
func getURLSRPMsWrapper(specsDir, distTag, buildDir, outDir, workerTar string, workers int, nestedSourcesDir, runCheck bool, packList string, templateSrcConfig sourceRetrievalConfiguration) (result []string, err error) {
	var chroot *safechroot.Chroot
	originalOutDir := outDir
	var packageURL []string
	if workerTar != "" {
		const leaveFilesOnDisk = false
		chroot, buildDir, outDir, specsDir, err = createChroot(workerTar, buildDir, outDir, specsDir)
		if err != nil {
			return
		}
		defer chroot.Close(leaveFilesOnDisk)
	}

	doCreateAll := func() error {
		packageURL, err = getURLSRPMs(specsDir, distTag, buildDir, outDir, workers, nestedSourcesDir, runCheck, packList, templateSrcConfig)
		return err
	}

	if chroot != nil {
		logger.Log.Info("Grabbing SRPMs URL inside a chroot environment")
		err = chroot.Run(doCreateAll)
	} else {
		logger.Log.Info("Grabbing SRPMs URL SRPMs in the host environment")
		err = doCreateAll()
	}

	if err != nil {
		return
	}

	// If this is container build then the bind mounts will not have been created.
	// Copy the chroot output to host output folder.
	if !buildpipeline.IsRegularBuild() {
		srpmsInChroot := filepath.Join(chroot.RootDir(), outDir)
		err = directory.CopyContents(srpmsInChroot, originalOutDir)
	}

	result = packageURL

	return
}

// createAllSRPMs will find all SPEC files in specsDir and pack SRPMs for them if needed.
func getURLSRPMs(specsDir, distTag, buildDir, outDir string, workers int, nestedSourcesDir, runCheck bool, specfile string, templateSrcConfig sourceRetrievalConfiguration) (result []string, err error) {
	const (
		emptyQueryFormat      = ``
		querySrpm             = `%{NAME}-%{VERSION}-%{RELEASE}.src.rpm`
		queryProvidedPackages = `rpm %{ARCH}/%{nvra}.rpm\n[provides %{PROVIDENEVRS}\n][requires %{REQUIRENEVRS}\n][arch %{ARCH}\n]`
	)
	// Find the SRPM that this SPEC will produce.
	defines := rpm.DefaultDefines(runCheck)
	defines[rpm.DistTagDefine] = distTag

	logger.Log.Infof("Finding SPEC's SRPM URL")
	sourcedir := filepath.Dir(specfile)

	pathstr := strings.Split(specfile, "/")
	spec := pathstr[len(pathstr)-1]
	//spec = "cri-o.spec"
	specsplice := strings.Split(spec, ".")
	spec2 := specsplice[0]

	spec = "/specs/" + spec2 + "/" + spec
	// Find the SRPM associated with the SPEC.
	return rpm.QuerySPEC(spec, sourcedir, querySrpm, defines, rpm.QueryHeaderArgument)

	// rpmspec -q $${spec_file} --srpm --define='with_check 1' --define='dist $(DIST_TAG)' --queryformat %{NAME}-%{VERSION}-%{RELEASE}.src.rpm
}

// createChroot creates a chroot to pack SRPMs inside of.
func createChroot(workerTar, buildDir, outDir, specsDir string) (chroot *safechroot.Chroot, newBuildDir, newOutDir, newSpecsDir string, err error) {
	const (
		chrootName       = "srpmpacker_chroot"
		existingDir      = false
		leaveFilesOnDisk = false

		outMountPoint    = "/output"
		specsMountPoint  = "/specs"
		buildDirInChroot = "/build"
	)

	extraMountPoints := []*safechroot.MountPoint{
		safechroot.NewMountPoint(outDir, outMountPoint, "", safechroot.BindMountPointFlags, ""),
		safechroot.NewMountPoint(specsDir, specsMountPoint, "", safechroot.BindMountPointFlags, ""),
	}

	extraDirectories := []string{
		buildDirInChroot,
	}

	newBuildDir = buildDirInChroot
	newOutDir = outMountPoint
	newSpecsDir = specsMountPoint

	chrootDir := filepath.Join(buildDir, chrootName)
	chroot = safechroot.NewChroot(chrootDir, existingDir)

	err = chroot.Initialize(workerTar, extraDirectories, extraMountPoints)
	if err != nil {
		return
	}

	defer func() {
		if err != nil {
			closeErr := chroot.Close(leaveFilesOnDisk)
			if closeErr != nil {
				logger.Log.Errorf("Failed to close chroot, err: %s", closeErr)
			}
		}
	}()

	// If this is container build then the bind mounts will not have been created.
	if !buildpipeline.IsRegularBuild() {
		// Copy in all of the SPECs so they can be packed.
		specsInChroot := filepath.Join(chroot.RootDir(), newSpecsDir)
		err = directory.CopyContents(specsDir, specsInChroot)
		if err != nil {
			return
		}

		// Copy any prepacked srpms so they will not be repacked.
		srpmsInChroot := filepath.Join(chroot.RootDir(), newOutDir)
		err = directory.CopyContents(outDir, srpmsInChroot)
		if err != nil {
			return
		}
	}

	// Networking support is needed to download sources.
	files := []safechroot.FileToCopy{
		{Src: "/etc/resolv.conf", Dest: "/etc/resolv.conf"},
	}

	err = chroot.AddFiles(files...)
	return
}
