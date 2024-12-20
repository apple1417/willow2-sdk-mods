#include "pch.h"
#include "parse_result.h"
#include <string_view>
#include "util.h"

namespace tml {

void ParseResult::discard_comments(void) {
    this->blimp_tags.clear();
    this->untagged_lines.clear();
}

void ParseResult::add_comment(const char* comment) {
    std::string_view comment_view{comment};

    if (comment_view.empty()) {
        return;
    }
    if (comment_view[0] != '@') {
        this->untagged_lines.emplace_back(to_system_encoding_py_str(comment));
        return;
    }

    auto space_idx = comment_view.find_first_of(' ');
    if (space_idx == 1) {
        // Malformed tag
        return;
    }

    auto tag = comment_view.substr(0, space_idx);
    auto value = space_idx == std::string_view::npos ? "" : comment_view.substr(space_idx + 1);

    std::string tag_lower(tag.size(), '\0');
    std::ranges::transform(tag, tag_lower.begin(), [](char chr) { return std::tolower(chr); });
    auto py_tag = to_system_encoding_py_str(tag_lower);

    if (!this->blimp_tags.contains(py_tag)) {
        this->blimp_tags[py_tag] = py::list{};
    }
    // Can safely use value.data() since it goes to the end of the string, we know it's null
    // terminated
    py::cast<py::list>(this->blimp_tags[py_tag]).append(to_system_encoding_py_str(value.data()));
}
void ParseResult::add_comment(const std::string& comment) {
    // Slightly awkward copy paste of the above, not really worth combining though
    if (comment.empty()) {
        return;
    }
    if (comment[0] != '@') {
        this->untagged_lines.emplace_back(to_system_encoding_py_str(comment));
        return;
    }

    auto space_idx = comment.find_first_of(' ');
    if (space_idx == 1) {
        // Malformed tag
        return;
    }

    auto tag = std::string_view{comment}.substr(0, space_idx);
    auto value =
        space_idx == std::string_view::npos ? "" : std::string_view{comment}.substr(space_idx + 1);

    std::string tag_lower(tag.size(), '\0');
    std::ranges::transform(tag, tag_lower.begin(), [](char chr) { return std::tolower(chr); });
    auto py_tag = to_system_encoding_py_str(tag_lower);

    if (!this->blimp_tags.contains(py_tag)) {
        this->blimp_tags[py_tag] = py::list{};
    }
    // Can safely use value.data() since it goes to the end of the string, we know it's null
    // terminated
    py::cast<py::list>(this->blimp_tags[py_tag]).append(to_system_encoding_py_str(value.data()));
}

}  // namespace tml
