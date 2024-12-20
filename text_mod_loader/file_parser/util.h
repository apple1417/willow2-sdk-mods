#ifndef FILE_PARSER_UTIL_H
#define FILE_PARSER_UTIL_H

#include "pch.h"

namespace tml {

// Traits class which compares case-insensitively
struct CaseInsensitiveTraits : public std::char_traits<char> {
    static bool eq(char chr_a, char chr_b);
    static bool lt(char chr_a, char chr_b);
    static int compare(const char* chr_a, const char* chr_b, size_t n);
};
struct CaseInsensitiveString : public std::basic_string<char, CaseInsensitiveTraits> {
    using std::basic_string<char, CaseInsensitiveTraits>::basic_string;

    CaseInsensitiveString(std::string_view str);
};
struct CaseInsensitiveStringView : public std::basic_string_view<char, CaseInsensitiveTraits> {
    using std::basic_string_view<char, CaseInsensitiveTraits>::basic_string_view;

    CaseInsensitiveStringView(std::string_view str);
    bool operator==(std::string_view str) const;
};

/**
 * @brief Creates a python string using the system encoding.
 *
 * @param str The string to convert.
 * @return The python string.
 */
py::str to_system_encoding_py_str(const char* str);
py::str to_system_encoding_py_str(const std::string& str);

/**
 * @brief Checks if the given line should be considered a command.
 *
 * @param str The line to check.
 * @param allow_spark True if bl3 style "Spark*"" commands should count.
 * @return True if it holds a command
 */
bool is_command(CaseInsensitiveStringView str, bool allow_spark = false);

}  // namespace tml

#endif /* FILE_PARSER_UTIL_H */
