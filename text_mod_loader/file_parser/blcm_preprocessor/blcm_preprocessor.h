#ifndef BLCM_PREPROCESSOR_H
#define BLCM_PREPROCESSOR_H

#include <iostream>
#include <stdexcept>
#include <string_view>

namespace blcm_preprocessor {

class ParserError : public std::runtime_error {
    using std::runtime_error::runtime_error;
};

/**
 * @brief Preprocesses a BLCMM file into valid xml.
 * @note Leaves the stream directly after the line with the closing `</BLCMM>` tag.
 * @note BLCMM files use the system codepage, in case you need to translate encoding later. As all
 *       structure is ASCII, this function has no issues with files using these characters.
 *
 * @param blcmm_input The stream containing a blcm file to consume as input.
 * @param xml_output The stream to output valid xml into.
 */
void preprocess(std::istream& blcmm_input, std::ostream& xml_output);

/**
 * @brief Checks if a string is in a comma separated list.
 * @note Intended to be used to check if a command is active in the current profile.
 *
 * @param value The value to search for.
 * @param list The comma separated list to search through.
 * @return True if the value is found in the list, false otherwise.
 */
bool in_comma_separated_list(std::string_view value, std::string_view list);

}  // namespace blcm_preprocessor

#endif /* BLCM_PREPROCESSOR_H */
