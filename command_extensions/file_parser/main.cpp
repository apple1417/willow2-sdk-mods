#include "pch.h"
#include "blcm_parser.h"
#include "blcm_preprocessor/blcm_preprocessor.h"
#include "line_parser.h"
#include "matcher.h"

namespace ce {

namespace {

/**
 * @brief Creates a python FileNotFoundError.
 *
 * @param filename The file which wasn't found.
 * @return An exception to throw.
 */
pybind11::error_already_set file_not_found(const std::filesystem::path& filename) {
#ifdef _WIN32
    PyErr_SetExcFromWindowsErrWithFilename(PyExc_FileNotFoundError, ERROR_FILE_NOT_FOUND,
                                           filename.string().c_str());
#else
    errno = ENOENT;
    PyErr_SetFromErrnoWithFilename(PyExc_FileNotFoundError, filename.string().c_str());
#endif
    return {};
}

}  // namespace

PYBIND11_MODULE(file_parser, mod) {
    py::register_exception<blcm_preprocessor::ParserError>(mod, "BLCMParserError",
                                                           PyExc_RuntimeError);

    py::enum_<EnableStrategy>(mod, "EnableStrategy")
        .value("All", EnableStrategy::ALL)
        .value("Any", EnableStrategy::ANY)
        .value("Force", EnableStrategy::FORCE)
        .value("Next", EnableStrategy::NEXT);

    mod.def(
        "parse",
        [](const std::filesystem::path& file_path) {
            if (!std::filesystem::exists(file_path)) {
                throw file_not_found(file_path);
            }

            std::ifstream file{file_path};

            std::string line;
            std::getline(file, line);
            file.seekg(0);

            std::vector<CommandMatch> matches{};
            if (line.starts_with("<BLCMM")) {
                matches = parse_blcmm_file(file);
            } else {
                matches = parse_file_line_by_line(file);
            }

            std::vector<py::tuple> output;
            std::ranges::transform(matches, std::back_inserter(output), [](auto& match) {
                return py::make_tuple(match.py_cmd, match.line, match.cmd_len);
            });

            return output;
        },
        "Parses custom commands out of mod file.\n"
        "\n"
        "Must have called update_commands() first, otherwise this won't match anything.\n"
        "\n"
        "Args:\n"
        "    file_path: The file to parse.\n"
        "Returns:\n"
        "    A list of 3-tuples, of the raw command name, the full line, and the command length.",
        "file_path"_a);

    mod.def("update_commands", update_commands,
            "Updates the commands which are matched by parse().\n"
            "\n"
            "Args:\n"
            "    commands: The commands to match.",
            "commands"_a);
}

}  // namespace ce
