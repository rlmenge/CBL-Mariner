// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

//TO DO
// ADD TLS certs for srpm servers that need them
// Bug in SRPM_URL_LIST where setting the URL to use 1.0 still curls a .cm2 srpm (fails when same cmd runs outside of toolkit)

package main

import (
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
	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/srpm"

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
	srpmUrlList  = app.Flag("srpm-url-list", "urls for SRPM repo.").String()
	srpmListFile = app.Flag("srpm-list", "Path to a list of SPECs to pack. If empty will pack all SPECs.").ExistingFile()

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
	srpmList, err := srpm.ParsePackListFile(*srpmListFile)
	logger.PanicOnError(err)

	logger.Log.Infof("SRPM list %s", srpmList)

	err = getSRPMQueryWrapper(*specsDir, *distTag, *buildDir, *outDir, *workerTar, *workers, *srpmUrlList, *runCheck, srpmList)
	logger.PanicOnError(err)

}

// getSRPMQueryWrapper wraps getSRPMQuery to conditionally run it inside a chroot.
// If workerTar is non-empty, packing will occur inside a chroot, otherwise it will run on the host system.
func getSRPMQueryWrapper(specsDir, distTag, buildDir, outDir, workerTar string, workers int, srpmUrlList string, runCheck bool, srpmList []string) (err error) {
	var chroot *safechroot.Chroot
	originalOutDir := outDir
	if workerTar != "" {
		const leaveFilesOnDisk = false
		chroot, buildDir, outDir, specsDir, err = srpm.CreateChroot(workerTar, buildDir, outDir, specsDir)
		if err != nil {
			return
		}
		defer chroot.Close(leaveFilesOnDisk)
	}

	doCreateAll := func() error {
		err = getSRPMQuery(specsDir, distTag, buildDir, outDir, workers, srpmUrlList, runCheck, srpmList)
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
func getSRPMQuery(specsDir, distTag, buildDir, outDir string, workers int, srpmUrlList string, runCheck bool, srpmList []string) (err error) {
	const (
		emptyQueryFormat = ``
		querySrpm        = `%{NAME}-%{VERSION}-%{RELEASE}.src.rpm`
	)
	// Find the SRPM that this SPEC will produce.
	defines := rpm.DefaultDefines(runCheck)
	defines[rpm.DistTagDefine] = distTag
	arch, err := rpm.GetRpmArch(runtime.GOARCH)
	if err != nil {
		logger.Log.Warn(err)
		return
	}
	specFiles, err := srpm.FindSPECFiles(specsDir, srpmList)
	if err != nil {
		return
	}

	// Assumes that srpmUrlList come in as ',' seperated
	urls := strings.Split(srpmUrlList, ",")
	for _, n := range urls {
		logger.Log.Infof("%s", n)
	}

	notFoundSRPMFlag := true
	for _, specfile := range specFiles {

		sourcedir := filepath.Dir(specfile)
		logger.Log.Infof("specfile for %s", specfile)
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
			logger.Log.Infof("%s", srpmURL)
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
