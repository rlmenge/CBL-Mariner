package srpm

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/microsoft/CBL-Mariner/toolkit/tools/internal/logger"
)

// RemoveDuplicateStrings will remove duplicate entries from a string slice
func RemoveDuplicateStrings(packList []string) (deduplicatedPackList []string) {
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

// ParsePackListFile will parse a list of packages to pack if one is specified.
// Duplicate list entries in the file will be removed.
func ParsePackListFile(packListFile string) (packList []string, err error) {
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

	if len(packList) == 0 {
		err = fmt.Errorf("cannot have empty pack list (%s)", packListFile)
	}

	packList = RemoveDuplicateStrings(packList)

	return
}

// FindSPECFiles finds all SPEC files that should be considered for packing.
// Takes into consideration a packList if provided.
func FindSPECFiles(specsDir string, packList []string) (specFiles []string, err error) {
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
