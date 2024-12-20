#include "pch.h"
#include "blcm_parser.h"
#include "blcm_preprocessor/blcm_preprocessor.h"
#include "util.h"

namespace tml {

namespace {

/**
 * @brief Extracts the description comments from a blcmm file.
 *
 * @param doc The parsed xml document.
 * @return A list of extracted comments.
 */
std::vector<py::str> extract_description(pugi::xml_document& doc) {
    const std::string_view version = doc.select_node("/BLCMM/@v").attribute().as_string();
    if (version != "1") {
        throw blcm_preprocessor::ParserError("Unknown BLCMM file version");
    }

    auto root = doc.select_node("/BLCMM/body/category").node();
    if (root == nullptr) {
        throw blcm_preprocessor::ParserError("Couldn't find root category");
    }

    std::vector<py::str> comments;
    for (auto child : root) {
        const CaseInsensitiveStringView child_name = child.name();

        static const constexpr CaseInsensitiveStringView comment = "comment";
        if (child_name == comment) {
            auto comment = child.child_value();
            if (is_command(comment)) {
                // This comment was really holding a command, the description's over
                break;
            }
            comments.emplace_back(to_system_encoding_py_str(comment));
            continue;
        }

        static const constexpr CaseInsensitiveStringView category = "category";
        if (child_name == category) {
            CaseInsensitiveStringView category_name = child.attribute("name").as_string();

            static const constexpr CaseInsensitiveStringView description = "description";
            if (category_name.find(description) == CaseInsensitiveStringView::npos) {
                // If this isn't a description category, the description's over
                break;
            }

            // This is a dedicated description category
            // Discard existing comments, and get them from this category's children instead
            comments.clear();

            for (auto grandchild : child) {
                const std::string_view grandchild_name = grandchild.name();
                if (grandchild_name == "comment") {
                    auto comment = grandchild.child_value();
                    if (is_command(comment)) {
                        break;
                    }
                    comments.emplace_back(to_system_encoding_py_str(comment));
                    continue;
                }

                // In the nested category, anything that's not a comment ends the description
                break;
            }
        }

        // After any non-comment, the description's over
        break;
    }

    return comments;
}

}  // namespace

std::pair<std::vector<py::str>, std::optional<py::str>> parse_blcmm_file(std::istream& stream) {
    std::stringstream processed_xml{};
    blcm_preprocessor::preprocess(stream, processed_xml);
    // Move the string out of the stream
    auto processed_str = std::move(processed_xml).str();

    pugi::xml_document doc{};
    // Use latin1 to try avoid any char conversions
    auto res = doc.load_buffer_inplace(processed_str.data(), processed_str.size(),
                                       pugi::parse_default, pugi::encoding_latin1);
    if (res.status != pugi::status_ok) {
        throw blcm_preprocessor::ParserError(res.description());
    }

    auto game_attr = doc.select_node("/BLCMM/head/type/@name").attribute().as_string();
    std::optional<py::str> game;

    // If not an empty string
    if (game_attr[0] != '\0') {
        game = to_system_encoding_py_str(game_attr);
    }

    return {extract_description(doc), std::move(game)};
}

}  // namespace tml
