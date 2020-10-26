# This file is part of BenchExec, a framework for reliable benchmarking:
# https://github.com/sosy-lab/benchexec
#
# SPDX-FileCopyrightText: 2007-2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import os
import benchexec.tools.template
import benchexec.result as result
from benchexec.tools.template import ToolNotFoundException


class Tool(benchexec.tools.template.BaseTool2):
    """
    This class serves as tool adaptor for Map2Check (https://github.com/hbgit/Map2Check)
    """

    REQUIRED_PATHS_6 = [
        "__init__.py",
        "map2check.py",
        "map2check-wrapper.sh",
        "modules",
    ]

    REQUIRED_PATHS_7_1 = ["map2check", "map2check-wrapper.py", "bin", "include", "lib"]

    def executable(self, tool_locator):
        # This is used in _get_version
        self._tool_locator = tool_locator

        # Relative path to map2check wrapper
        if self._get_version() == 6:
            return tool_locator.find_executable("map2check-wrapper.sh")
        elif self._get_version() > 6:
            return tool_locator.find_executable("map2check-wrapper.py")
        assert False, "Unexpected version " + self._get_version()

    def program_files(self, executable):
        """
        Determine the file paths to be adopted
        """
        if self._get_version() == 6:
            paths = self.REQUIRED_PATHS_6
        elif self._get_version() > 6:
            paths = self.REQUIRED_PATHS_7_1

        return paths

    def _get_version(self):
        """
        Determine the version based on map2check-wrapper.sh file
        """
        try:
            self._tool_locator.find_executable("map2check-wrapper.sh")
            return 6
        except ToolNotFoundException:
            return 7

    def working_directory(self, executable):
        executableDir = os.path.dirname(executable)
        return executableDir

    def version(self, executable):
        return self._version_from_tool(executable)

    def name(self):
        return "Map2Check"

    def cmdline(self, executable, options, task, rlimits):
        sourcefiles = list(task.input_files_or_identifier)

        assert len(sourcefiles) == 1, "only one sourcefile supported"
        assert task.property_file, "property file required"

        sourcefile = sourcefiles[0]
        if self._get_version() == 6:
            return [executable] + options + ["-c", task.property_file, sourcefile]
        elif self._get_version() > 6:
            return [executable] + options + ["-p", task.property_file, sourcefile]
        assert False, "Unexpected version " + self._get_version()

    def determine_result(self, run):
        output = run.output
        if not output:
            return result.RESULT_UNKNOWN
        output = output[-1].strip()
        status = result.RESULT_UNKNOWN

        if self._get_version() > 6:
            if output.endswith("TRUE"):
                status = result.RESULT_TRUE_PROP
            elif "FALSE" in output:
                if "FALSE_MEMTRACK" in output:
                    status = result.RESULT_FALSE_MEMTRACK
                elif "FALSE_MEMCLEANUP" in output:
                    status = result.RESULT_FALSE_MEMCLEANUP
                elif "FALSE_DEREF" in output:
                    status = result.RESULT_FALSE_DEREF
                elif "FALSE_FREE" in output:
                    status = result.RESULT_FALSE_FREE
                elif "FALSE_OVERFLOW" in output:
                    status = result.RESULT_FALSE_OVERFLOW
                else:
                    status = result.RESULT_FALSE_REACH
            elif output.endswith("UNKNOWN"):
                status = result.RESULT_UNKNOWN
            elif run.was_timeout:
                status = "TIMEOUT"
            else:
                status = "ERROR"

        elif self._get_version() == 6:
            if output.endswith("TRUE"):
                status = result.RESULT_TRUE_PROP
            elif "FALSE" in output:
                if "FALSE(valid-memtrack)" in output:
                    status = result.RESULT_FALSE_MEMTRACK
                elif "FALSE(valid-deref)" in output:
                    status = result.RESULT_FALSE_DEREF
                elif "FALSE(valid-free)" in output:
                    status = result.RESULT_FALSE_FREE
            elif output.endswith("UNKNOWN"):
                status = result.RESULT_UNKNOWN
            elif run.was_timeout:
                status = "TIMEOUT"
            else:
                status = "ERROR"

        return status
