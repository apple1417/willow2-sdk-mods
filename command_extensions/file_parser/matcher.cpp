#include "pch.h"
#include "matcher.h"

namespace ce {

#pragma region Case insensitive String

bool CaseInsensitiveTraits::eq(char chr_a, char chr_b) {
    return std::tolower(chr_a) == std::tolower(chr_b);
}
bool CaseInsensitiveTraits::lt(char chr_a, char chr_b) {
    return std::tolower(chr_a) < std::tolower(chr_b);
}
int CaseInsensitiveTraits::compare(const char* chr_a, const char* chr_b, size_t n) {
    while (n-- != 0) {
        if (std::tolower(*chr_a) < std::tolower(*chr_b)) {
            return -1;
        }
        if (std::tolower(*chr_a) > std::tolower(*chr_b)) {
            return 1;
        }
        ++chr_a;
        ++chr_b;
    }
    return 0;
}

CaseInsensitiveString::CaseInsensitiveString(std::string_view str)
    : CaseInsensitiveString(str.data(), str.size()) {}

CaseInsensitiveStringView::CaseInsensitiveStringView(std::string_view str)
    : CaseInsensitiveStringView(str.data(), str.size()) {}

bool CaseInsensitiveStringView::operator==(std::string_view str) const {
    return *this == CaseInsensitiveStringView{str.data(), str.size()};
}

#pragma endregion

#pragma region Command List

namespace {

// To match strings somewhat efficiently we'll use a binary search - while not profiled I don't
// think we have enough strings and enough matching prefixes to make a full radix trie worth it.

// For this we need to keep our list of commands sorted.
std::vector<CaseInsensitiveString> sorted_commands;

}  // namespace

void update_commands(const std::vector<std::string_view>& commands) {
    sorted_commands.clear();
    sorted_commands.reserve(commands.size());

    std::ranges::transform(commands, std::back_inserter(sorted_commands),
                           [](auto cmd) { return CaseInsensitiveString{cmd}; });
    std::ranges::sort(sorted_commands);
}

void add_new_command(CaseInsensitiveStringView cmd) {
    auto non_space = std::ranges::find_if_not(cmd, [](auto chr) { return std::isspace(chr); });
    if (non_space == cmd.end()) {
        return;
    }
    auto cmd_name_end =
        std::find_if(non_space, cmd.end(), [](auto chr) { return std::isspace(chr); });
    if (cmd_name_end != cmd.end()) {
        // Make sure there are no extra characters after this
        auto next_char =
            std::find_if_not(cmd_name_end, cmd.end(), [](auto chr) { return std::isspace(chr); });
        if (next_char != cmd.end()) {
            // Give up
            return;
        }
    }

    CaseInsensitiveString cmd_name{non_space, cmd_name_end};
    sorted_commands.insert(std::ranges::lower_bound(sorted_commands, cmd_name),
                           std::move(cmd_name));
}

#pragma endregion

std::pair<std::string_view, CommandMatch> try_match_command(std::string_view line) {
    auto non_space = std::ranges::find_if_not(line, [](auto chr) { return std::isspace(chr); });
    if (non_space == line.end()) {
        return {};
    }

    auto cmd_end = std::find_if(non_space, line.end(), [](auto chr) { return std::isspace(chr); });

    // NOLINTNEXTLINE(modernize-use-ranges)
    if (!std::binary_search(sorted_commands.begin(), sorted_commands.end(),
                            CaseInsensitiveStringView{non_space, cmd_end})) {
        return {};
    }

    // We want to use these Python conversion functions since they automatically handle the locale
    // for us (using the system one like blcmm does)
    // Unfortunately Python requires a null terminator :/
    std::string cmd_str{non_space, cmd_end};
    std::string line_str{line};

    const CommandMatch match{
        .py_cmd = py::reinterpret_steal<py::object>(PyUnicode_DecodeLocaleAndSize(
            cmd_str.data(), static_cast<Py_ssize_t>(cmd_str.size()), nullptr)),
        .line = py::reinterpret_steal<py::object>(PyUnicode_DecodeLocaleAndSize(
            line_str.data(), static_cast<Py_ssize_t>(line_str.size()), nullptr)),
        .cmd_len = cmd_end - line.begin()};

    return std::make_pair(std::string_view{non_space, cmd_end}, match);
}

}  // namespace ce
