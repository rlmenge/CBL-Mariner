// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//TO DO
// do I need certs? I think no
// fix srpm url lists handling. How do I test?
// why do I need to mv instead of specifiying the output dir for wget?
// keep wget in main?

package main

import (
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

const (
	defaultBuildDir    = "./build/SRPMS"
	defaultWorkerCount = "10"
)

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
	specInput      = app.Flag("spec-input", "Spec that needs SRPM.").String()
	srpmSourceURLs = app.Flag("srpm-source-urls", "urls for SRPM.").String()

	workerTar = app.Flag("worker-tar", "Full path to worker_chroot.tar.gz. If this argument is empty, SRPMs will be packed in the host environment.").ExistingFile()
)

func main() {
	app.Version(exe.ToolkitVersion)
	kingpin.MustParse(app.Parse(os.Args[1:]))
	logger.InitBestEffort(*logFile, *logLevel)
	logger.Log.Infof("Downloading SRPM for %s", *specInput)

	if *workers <= 0 {
		logger.Log.Fatalf("Value in --workers must be greater than zero. Found %d", *workers)
	}

	// Setup remote source configuration
	var err error
	var packageSRPM string

	//spec := "/home/rachel/repos/CBL-Mariner-test/SPECS/iptables/iptables.spec"

	packageSRPM, err = getSRPMQueryWrapper(*specsDir, *distTag, *buildDir, *outDir, *workerTar, *workers, *nestedSourcesDir, *runCheck, *specInput)
	logger.PanicOnError(err)

	// Assumes that srpmSourceURLs come in as ',' seperated
	urls := strings.Split(*srpmSourceURLs, ",")
	// for _, n := range urls {
	// 	logger.Log.Infof("%s", n)
	// }

	for _, url := range urls {
		srpmURL := url + "/" + packageSRPM

		wgetArgs := []string{
			srpmURL,
		}
		_, stderr, err := shell.Execute("wget", wgetArgs...)
		if err != nil {
			logger.Log.Warn(stderr)
		} else {
			mvArgs := []string{
				packageSRPM,
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

// getSRPMQueryWrapper wraps getSRPMQuery to conditionally run it inside a chroot.
// If workerTar is non-empty, packing will occur inside a chroot, otherwise it will run on the host system.
func getSRPMQueryWrapper(specsDir, distTag, buildDir, outDir, workerTar string, workers int, nestedSourcesDir, runCheck bool, packList string) (result string, err error) {
	var chroot *safechroot.Chroot
	originalOutDir := outDir
	var querySRPMResult []string
	if workerTar != "" {
		const leaveFilesOnDisk = false
		chroot, buildDir, outDir, specsDir, err = createChroot(workerTar, buildDir, outDir, specsDir)
		if err != nil {
			return
		}
		defer chroot.Close(leaveFilesOnDisk)
	}

	doCreateAll := func() error {
		querySRPMResult, err = getSRPMQuery(specsDir, distTag, buildDir, outDir, workers, nestedSourcesDir, runCheck, packList)
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

	result = querySRPMResult[0]

	return
}

// getSRPMQuery queries for the name, version and release of the SRPM
func getSRPMQuery(specsDir, distTag, buildDir, outDir string, workers int, nestedSourcesDir, runCheck bool, specfile string) (result []string, err error) {
	const (
		emptyQueryFormat = ``
		querySrpm        = `%{NAME}-%{VERSION}-%{RELEASE}.src.rpm`
	)
	// Find the SRPM that this SPEC will produce.
	defines := rpm.DefaultDefines(runCheck)
	defines[rpm.DistTagDefine] = distTag

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
