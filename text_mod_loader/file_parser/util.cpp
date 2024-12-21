#include "pch.h"
#include "util.h"

namespace tml {

#pragma region Case insensitive string

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

py::str to_system_encoding_py_str(const char* str) {
    return py::reinterpret_steal<py::object>(
        PyUnicode_DecodeLocaleAndSize(str, (Py_ssize_t)std::strlen(str), nullptr));
}

py::str to_system_encoding_py_str(const std::string& str) {
    return py::reinterpret_steal<py::object>(
        PyUnicode_DecodeLocaleAndSize(str.data(), (Py_ssize_t)str.size(), nullptr));
}

bool is_command(CaseInsensitiveStringView str, bool allow_spark) {
    auto non_space = std::ranges::find_if_not(str, [](auto chr) { return std::isspace(chr); });
    if (non_space == str.end()) {
        return false;
    }

    // Don't bother getting the full first word for this one, since we expect "SparkLevelPatchEntry"
    // and the like
    if (allow_spark && CaseInsensitiveStringView{non_space, str.end()}.starts_with("spark")) {
        return true;
    }

    auto word_end = std::find_if(non_space, str.end(), [](auto chr) { return std::isspace(chr); });
    const CaseInsensitiveStringView first_word{non_space, word_end};
    return first_word == "say" || first_word == "exec" || first_word == "set";
}

}  // namespace tml
