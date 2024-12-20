#include "pch.h"
#include "blcm_parser.h"
#include "blcm_preprocessor/blcm_preprocessor.h"
#include "filtertool_parser.h"
#include "line_parser.h"
#include "parse_result.h"
#include "util.h"

namespace tml {

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

/**
 * @brief Looks through an input stream for commands matching hotfix ones, and extracts the service.
 *
 * @param input The input stream to look though.
 * @param parse_result The parse result struct to extract the spark service index into.
 */
void look_for_spark_service(std::istream& input, ParseResult& parse_result) {
    for (std::string line; std::getline(input, line);) {
        // Aproximately matching the regex:
        // /\s+set\s+Transient.SparkServiceConfiguration_\d+\s+(keys|values)/i

        const constexpr CaseInsensitiveStringView set = "set";
        const constexpr CaseInsensitiveStringView transient =
            "Transient.SparkServiceConfiguration_";
        const constexpr CaseInsensitiveStringView keys = "Keys";
        const constexpr CaseInsensitiveStringView values = "Values";

        CaseInsensitiveStringView line_view{line};
        auto set_offset = line_view.find(set);
        if (set_offset == std::string::npos) {
            continue;
        }

        auto transient_offset = line_view.find(transient, set_offset + set.size() + 1);
        if (transient_offset == std::string::npos) {
            continue;
        }

        auto transient_end = transient_offset + transient.size();

        size_t idx = 0;
        auto [ptr, ec] = std::from_chars(line_view.data() + transient_offset,
                                         line_view.data() + line_view.size(), idx);
        if (ec != std::errc{}) {
            continue;
        }

        auto keys_offset = line_view.find(keys, transient_end);
        auto values_offset = line_view.find(values, transient_end);
        if (keys_offset == std::string::npos && values_offset == std::string::npos) {
            continue;
        }

        parse_result.spark_service_idx = idx;
    }
}

/**
 * @brief Runs the file parser over the given stream.
 *
 * @param stream The stream to parse.
 * @return The result of parsing the stream.
 */
ParseResult parse(std::istream& stream) {
    std::string line;
    std::getline(stream, line);
    stream.seekg(0);

    ParseResult parse_result;

    if (line.starts_with("<BLCMM")) {
        parse_blcmm_file(stream, parse_result);
    } else if (line.starts_with("#<")) {
        parse_filtertool_file(stream, parse_result);
    } else {
        parse_file_line_by_line(stream, parse_result);
    }

    look_for_spark_service(stream, parse_result);

    return parse_result;
}

}  // namespace

PYBIND11_MODULE(file_parser, mod) {
    py::register_exception<blcm_preprocessor::ParserError>(mod, "BLCMParserError",
                                                           PyExc_RuntimeError);

    py::class_<ParseResult>(mod, "ParseResult")
        .def_readwrite("blimp_tags", &ParseResult::blimp_tags)
        .def_readwrite("untagged_lines", &ParseResult::untagged_lines)
        .def_readwrite("game", &ParseResult::game)
        .def_readwrite("spark_service_idx", &ParseResult::spark_service_idx);

    mod.def(
        "parse",
        [](const std::filesystem::path& file_path) {
            if (!std::filesystem::exists(file_path)) {
                throw file_not_found(file_path);
            }
            std::ifstream file{file_path};
            return parse(file);
        },
        "Parses the tml-specific info out of mod file.\n"
        "\n"
        "Args:\n"
        "    file_path: The file to parse.\n"
        "Returns:\n"
        "    The parsing result.",
        "file_path"_a);

    mod.def(
        "parse_string",
        [](const std::string& str) {
            std::stringstream stream{str};
            return parse(stream);
        },
        "Parses the tml-specific info out of a string.\n"
        "\n"
        "Args:\n"
        "    string: The string to parse.\n"
        "Returns:\n"
        "    The parsing result.",
        "string"_a);
}

}  // namespace tml
