#include "blcm_preprocessor.h"

#include <cctype>
#include <format>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace blcm_preprocessor {

namespace {

constexpr std::string_view FILTERTOOL_WARNING =
    "#<!!!You opened a file saved with BLCMM in FilterTool. Please update to BLCMM to properly "
    "open this file!!!>";

/**
 * @brief Adds a character to the stream, xml escaping if needed.
 *
 * @param chr The character to add.
 * @param stream The stream to write to.
 */
constexpr void put_xml_escaped(char chr, std::ostream& stream) {
    switch (chr) {
        case '"':
            stream << "&quot;";
            break;
        case '\'':
            stream << "&apos;";
            break;
        case '<':
            stream << "&lt;";
            break;
        case '>':
            stream << "&gt;";
            break;
        case '&':
            stream << "&amp;";
            break;
        default:
            stream << chr;
            break;
    }
}

struct RootTagState {
    std::string tag;
    size_t nest_count = 0;

    /**
     * @brief Checks if the document has started.
     *
     * @return True if we've seen the root tag.
     */
    [[nodiscard]] bool started(void) const { return !this->tag.empty(); }
};

/**
 * @brief Processes root tags and checks if the document's closed.
 *
 * @param tag_name The current tag name.
 * @param root_tag_state Extra state needed for the processing.
 * @return True if the root tag has closed.
 */
bool check_root_tag_closed(std::string_view tag_name, RootTagState& root_tag_state) {
    if (!root_tag_state.started()) {
        // Just assume the first tag is opening, the XML parsing will fail if it's not anyway
        root_tag_state.tag = tag_name;
        root_tag_state.nest_count++;
        return false;
    }

    // Keep track of nested tags of the same type as the root
    if (tag_name == root_tag_state.tag) {
        root_tag_state.nest_count++;
    } else if (tag_name[0] == '/' && tag_name.substr(1) == root_tag_state.tag) {
        root_tag_state.nest_count--;
    }

    // If we make it back to 0, we've finished
    return root_tag_state.nest_count == 0;
}

/**
 * @brief Process though any attributes and return the start of the content.
 *
 * @param line The line to process.
 * @param xml_output The stream to output valid xml into.
 * @param tag_name_end The index into the line where the tag name ends.
 * @return The index into the line where the content starts.
 */
size_t process_attributes_and_get_content_start(std::string_view line,
                                                std::ostream& xml_output,
                                                size_t tag_name_end) {
    // If there was no whitespace at the end of the tag, return immediately
    if (line[tag_name_end] == '>') {
        return tag_name_end + 1;
    }

    auto tag_body_section_start = tag_name_end + 1;
    while (true) {
        // Grab all characters up to the next attribute value, or the end of the tag
        auto tag_body_section_end = line.find_first_of("\">", tag_body_section_start);
        if (tag_body_section_end > line.size()) {
            throw ParserError(std::format("Failed to parse line (tag doesn't close):\n{}", line));
        }

        xml_output << line.substr(tag_body_section_start,
                                  tag_body_section_end - tag_body_section_start + 1);

        // We found the end of the tag
        if (line[tag_body_section_end] == '>') {
            return tag_body_section_end + 1;
        }

        // Process through the attribute value until we find the end
        // We know the line must end in a `>`, so we can skip the last character to avoid going out
        // of bounds while checking for `\"`s
        bool finished_attribute = false;
        for (size_t idx = tag_body_section_end + 1; idx < (line.size() - 1); idx++) {
            auto chr = line[idx];
            if (chr == '\\' && line[idx + 1] == '"') {
                put_xml_escaped('"', xml_output);
                idx++;
                continue;
            }
            if (chr == '"') {
                xml_output << '"';
                tag_body_section_start = idx + 1;
                finished_attribute = true;
                break;
            }
            put_xml_escaped(chr, xml_output);
        }
        if (!finished_attribute) {
            throw ParserError(
                std::format("Failed to parse line (couldn't find end of attribute):\n{}", line));
        }
    }
}

/**
 * @brief Process though the content of a tag, after seeing the opening tag.
 *
 * @param line The line to process.
 * @param xml_output The stream to output valid xml into.
 * @param tag_name_end The index into the line where the tag name ends.
 */
void process_tag_content(std::string_view line,
                         std::ostream& xml_output,
                         std::string_view tag_name,
                         size_t content_start) {
    // We've not sure if we have a single or multiline tag yet
    // To avoid iterating twice, output until we get a non-whitespace char - if we get one it must
    // be a single line tag, if we reach the end of the string it must've been a multiline
    auto ittr = line.begin() + (std::string_view::difference_type)content_start;
    for (; ittr < line.end(); ittr++) {
        auto chr = *ittr;
        if (std::isspace(chr) == 0) {
            break;
        }
        xml_output << chr;
    }

    if (ittr == line.end()) {
        // Must be a multiline
        return;
    }

    const std::string_view content{ittr, line.end()};

    // Make sure the line ends with a valid closing tag
    auto closing_tag_start = content.rfind("</");
    if (closing_tag_start == std::string_view::npos
        || content.substr(closing_tag_start + 2, tag_name.size()) != tag_name) {
        throw ParserError(
            std::format("Failed to parse line (couldn't find closing tag):\n{}", line));
    }
    auto closing_tag_end =
        content.find_first_not_of(" \t", closing_tag_start + 2 + tag_name.size());
    if (closing_tag_end == std::string_view::npos || content[closing_tag_end] != '>') {
        throw ParserError(
            std::format("Failed to parse line (couldn't find closing tag):\n{}", line));
    }

    // Everything else must be part of the content
    for (const auto chr : content.substr(0, closing_tag_start)) {
        put_xml_escaped(chr, xml_output);
    }

    xml_output << "</" << tag_name << ">";
}

/**
 * @brief Preprocesses an individual line of a blcmm file.
 *
 * @param line The line to process
 * @param xml_output The stream to output valid xml into.
 * @param root_tag_state Extra state required by the root tag processing.
 * @return True while successfully processed, false after the end of the document.
 */
bool preprocess_line(std::string_view line,
                     std::ostream& xml_output,
                     RootTagState& root_tag_state) {
    auto tag_start = line.find_first_of('<');
    if (tag_start == std::string_view::npos) {
        throw ParserError(
            std::format("Failed to parse line (couldn't find initial tag):\n{}", line));
    }

    // Ignore the filtertool warning - which starts one char before the opening bracket
    if (tag_start > 0 && line.substr(tag_start - 1).starts_with(FILTERTOOL_WARNING)) {
        return true;
    }

    auto tag_name_end = line.find_first_of("> \t", tag_start);
    if (tag_name_end == std::string_view::npos) {
        throw ParserError(
            std::format("Failed to parse line (initial tag doesn't close):\n{}", line));
    }

    // Note this may include a leading `/` if looking at a closing tag
    auto tag_name = line.substr(tag_start + 1, tag_name_end - tag_start - 1);

    xml_output << '<' << tag_name << line[tag_name_end];

    if (check_root_tag_closed(tag_name, root_tag_state)) {
        // Add the closing `>` if we didn't previously
        if (line[tag_name_end] != '>') {
            xml_output << '>';
        }
        return false;
    }

    // If this was a closing tag (but not the root closing tag), we can still assume no attributes
    // and end here
    if (tag_name[0] == '/') {
        // Again may need to add the closing `>`
        if (line[tag_name_end] != '>') {
            xml_output << '>';
        }
        return true;
    }

    auto content_start = process_attributes_and_get_content_start(line, xml_output, tag_name_end);

    // If the tag was self closing, we can end here
    if (line[content_start - 2] == '/') {
        return true;
    }

    process_tag_content(line, xml_output, tag_name, content_start);
    return true;
}

}  // namespace

void preprocess(std::istream& blcmm_input, std::ostream& xml_output) {
    RootTagState root_tag_state{};

    for (std::string line;
         std::getline(blcmm_input, line) && preprocess_line(line, xml_output, root_tag_state);) {
        xml_output << std::flush;
    }

    if (blcmm_input.fail()) {
        if (blcmm_input.eof()) {
            if (root_tag_state.started()) {
                throw ParserError("IO Error while reading input (eof)");
            }
            // If we got EOF but didn't have an opening tag, it's an empty file, exit without error
        } else {
            throw ParserError("IO Error while reading input");
        }
    }

    if (xml_output.fail()) {
        throw ParserError("IO Error while writing output");
    }
}

bool in_comma_separated_list(std::string_view value, std::string_view list) {
    for (size_t entry_start = 0; entry_start < list.size();) {
        auto entry_end = list.find_first_of(',', entry_start);
        if (list.substr(entry_start, entry_end - entry_start) == value) {
            return true;
        }

        if (entry_end == std::string_view::npos) {
            break;
        }
        entry_start = entry_end + 1;
    }
    return false;
}

}  // namespace blcm_preprocessor
