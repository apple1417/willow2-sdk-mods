#include "pch.h"
#include "filtertool_parser.h"
#include "util.h"

namespace tml {

std::vector<py::str> parse_filtertool_file(std::istream& stream) {
    std::vector<py::str> comments;

    // Discard the first line (root category header)
    std::string line;
    std::getline(stream, line);

    auto started_description_category = false;
    for (; std::getline(stream, line);) {
        auto first_non_space =
            std::ranges::find_if_not(line, [](auto chr) { return std::isspace(chr); });
        auto last_non_space = std::find_if_not(line.rbegin(), line.rend(),
                                               [](auto chr) { return std::isspace(chr); });

        std::string_view trimmed{first_non_space, last_non_space.base()};

        if (trimmed.starts_with("#<") && trimmed.ends_with('>')) {
            if (!started_description_category) {
                CaseInsensitiveStringView category_name{trimmed.begin() + 2, trimmed.end() - 1};

                static const constexpr CaseInsensitiveStringView description = "description";
                if (category_name.find(description) != CaseInsensitiveStringView::npos) {
                    // This is a dedicated description category
                    // Discard existing comments, and get them from this category's children instead
                    comments.clear();
                    started_description_category = true;
                    continue;
                }
            }

        } else if (!is_command(trimmed)) {
            // Must be a comment, add to the list
            comments.emplace_back(to_system_encoding_py_str(line));
            continue;
        }

        // This is either a command, or a (non-description) category, which both mark the end of
        // the description.
        // Seek back to the start of this line, to leave the stream in a good state, then quit
        stream.seekg(-(ptrdiff_t)line.size(), std::ios::cur);
        break;
    }

    return comments;
}

}  // namespace tml
