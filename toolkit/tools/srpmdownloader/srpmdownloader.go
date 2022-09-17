// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//TO DO
// ADD TLS certs for srpm servers that need them
// Bug in SRPM_URL_LIST where setting the URL to use 1.0 still curls a .cm2 srpm (fails when same cmd runs outside of toolkit)
// Bug where the SRPM_PACK_LIST= will not clear srpm_pack_list_file ($(BUILD_SRPMS_DIR)/pack_list.txt) even if argument is empty
// A lot of code duplication w/ srpmpacker. Should make a library

package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
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

	workers = app.Flag("workers", "Number of concurrent goroutines to parse with.").Default(defaultWorkerCount).Int()

	// Use String() and not ExistingFile() as the Makefile may pass an empty string if the user did not specify any of these options
	srpmSourceURLs = app.Flag("srpm-source-urls", "urls for SRPM.").String()
	srpmListFile   = app.Flag("srpm-list", "Path to a list of SPECs to pack. If empty will pack all SPECs.").ExistingFile()

	workerTar = app.Flag("worker-tar", "Full path to worker_chroot.tar.gz. If this argument is empty, SRPMs will be packed in the host environment.").ExistingFile()
)

func main() {
	app.Version(exe.ToolkitVersion)
	kingpin.MustParse(app.Parse(os.Args[1:]))
	logger.InitBestEffort(*logFile, *logLevel)

	if *workers <= 0 {
		logger.Log.Fatalf("Value in --workers must be greater than zero. Found %d", *workers)
	}

	// Setup remote source configuration
	var err error

	// A pack list may be provided, if so only pack this subset.
	// If none is provided, pack all srpms.
	srpmList, err := parsePackListFile(*srpmListFile)
	logger.PanicOnError(err)

	logger.Log.Infof("SRPM list %s", srpmList)

	err = getSRPMQueryWrapper(*specsDir, *distTag, *buildDir, *outDir, *workerTar, *workers, *srpmSourceURLs, *runCheck, srpmList)
	logger.PanicOnError(err)

}

// removeDuplicateStrings will remove duplicate entries from a string slice
func removeDuplicateStrings(packList []string) (deduplicatedPackList []string) {
	var (
		packListSet = make(map[string]struct{})
		exists      = struct{}{}
	)

	for _, entry := range packList {
		packListSet[entry] = exists
	}

	for entry := range packListSet {
		deduplicatedPackList = append(deduplicatedPackList, entry)
	}

	return
}

// parsePackListFile will parse a list of packages to pack if one is specified.
// Duplicate list entries in the file will be removed.
func parsePackListFile(packListFile string) (packList []string, err error) {
	if packListFile == "" {
		return
	}

	file, err := os.Open(packListFile)
	if err != nil {
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" {
			packList = append(packList, line)
		}
	}

	// This is on in srpmpacker. However, this prevents empty lists
	// if len(packList) == 0 {
	// 	err = fmt.Errorf("cannot have empty pack list (%s)", packListFile)
	// }

	packList = removeDuplicateStrings(packList)

	return
}

// getSRPMQueryWrapper wraps getSRPMQuery to conditionally run it inside a chroot.
// If workerTar is non-empty, packing will occur inside a chroot, otherwise it will run on the host system.
func getSRPMQueryWrapper(specsDir, distTag, buildDir, outDir, workerTar string, workers int, srpmSourceURLs string, runCheck bool, srpmList []string) (err error) {
	var chroot *safechroot.Chroot
	originalOutDir := outDir
	if workerTar != "" {
		const leaveFilesOnDisk = false
		chroot, buildDir, outDir, specsDir, err = createChroot(workerTar, buildDir, outDir, specsDir)
		if err != nil {
			return
		}
		defer chroot.Close(leaveFilesOnDisk)
	}

	doCreateAll := func() error {
		err = getSRPMQuery(specsDir, distTag, buildDir, outDir, workers, srpmSourceURLs, runCheck, srpmList)
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

	return
}

// getSRPMQuery queries for the name, version and release of the SRPM
func getSRPMQuery(specsDir, distTag, buildDir, outDir string, workers int, srpmSourceURLs string, runCheck bool, srpmList []string) (err error) {
	const (
		emptyQueryFormat = ``
		querySrpm        = `%{NAME}-%{VERSION}-%{RELEASE}.src.rpm`
	)
	// Find the SRPM that this SPEC will produce.
	defines := rpm.DefaultDefines(runCheck)
	defines[rpm.DistTagDefine] = distTag
	arch, err := rpm.GetRpmArch(runtime.GOARCH)

	specFiles, err := findSPECFiles(specsDir, srpmList)
	if err != nil {
		return
	}

	// Assumes that srpmSourceURLs come in as ',' seperated
	urls := strings.Split(srpmSourceURLs, ",")
	for _, n := range urls {
		logger.Log.Infof("%s", n)
	}

	notFoundSRPMFlag := true
	for _, specfile := range specFiles {

		sourcedir := filepath.Dir(specfile)
		logger.Log.Infof("specfile for %s", specfile)
		logger.Log.Infof("outdir for %s", outDir)
		var packageSRPMs []string
		packageSRPMs, err = rpm.QuerySPEC(specfile, sourcedir, querySrpm, arch, defines, rpm.QueryHeaderArgument)
		if err != nil {
			logger.Log.Warn(err)
			return
		}

		packageSRPM := packageSRPMs[0]

		// Try each provided SRPM source server until SRPM is found
		for _, url := range urls {

			// Craft URL
			srpmURL := url + "/" + packageSRPM
			outputSpot := outDir + "/" + packageSRPM

			// curl URL
			curlArgs := []string{
				"-o",
				outputSpot,
				srpmURL,
			}

			var stderr string
			_, stderr, err = shell.Execute("curl", curlArgs...)
			if err != nil {
				logger.Log.Warn(err)
				logger.Log.Warn(stderr)
				err = nil
			} else {
				notFoundSRPMFlag = false
				break
			}
		}
		if notFoundSRPMFlag {
			err = fmt.Errorf("no srpm found %s", packageSRPM)
			return
		}
	}
	return
}

// findSPECFiles finds all SPEC files that should be considered for packing.
// Takes into consideration a packList if provided.
func findSPECFiles(specsDir string, packList []string) (specFiles []string, err error) {
	if len(packList) == 0 {
		specSearch := filepath.Join(specsDir, "**/*.spec")
		specFiles, err = filepath.Glob(specSearch)
	} else {
		for _, specName := range packList {
			var specFile []string

			specSearch := filepath.Join(specsDir, fmt.Sprintf("**/%s.spec", specName))
			specFile, err = filepath.Glob(specSearch)

			// If a SPEC is in the pack list, it must be packed.
			if err != nil {
				return
			}
			if len(specFile) != 1 {
				if strings.HasPrefix(specName, "msopenjdk-11") {
					logger.Log.Debugf("Ignoring missing match for '%s', which is externally-provided and thus doesn't have a local spec.", specName)
					continue
				} else {
					err = fmt.Errorf("unexpected number of matches (%d) for spec file (%s)", len(specFile), specName)
					return
				}
			}

			specFiles = append(specFiles, specFile[0])
		}
	}

	return
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
