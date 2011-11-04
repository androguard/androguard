// Copyright (C) 2006 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


/**
 * @fileoverview
 * some functions for browser-side pretty printing of code contained in html.
 *
 * The lexer should work on a number of languages including C and friends,
 * Java, Python, Bash, SQL, HTML, XML, CSS, Javascript, and Makefiles.
 * It works passably on Ruby, PHP and Awk and a decent subset of Perl, but,
 * because of commenting conventions, doesn't work on Smalltalk, Lisp-like, or
 * CAML-like languages.
 *
 * If there's a language not mentioned here, then I don't know it, and don't
 * know whether it works.  If it has a C-like, Bash-like, or XML-like syntax
 * then it should work passably.
 *
 * Usage:
 * 1) include this source file in an html page via
 * <script type="text/javascript" src="/path/to/prettify.js"></script>
 * 2) define style rules.  See the example page for examples.
 * 3) mark the <pre> and <code> tags in your source with class=prettyprint.
 *    You can also use the (html deprecated) <xmp> tag, but the pretty printer
 *    needs to do more substantial DOM manipulations to support that, so some
 *    css styles may not be preserved.
 * That's it.  I wanted to keep the API as simple as possible, so there's no
 * need to specify which language the code is in.
 *
 * Change log:
 * cbeust, 2006/08/22
 *   Java annotations (start with "@") are now captured as literals ("lit")
 */

// JSLint declarations
/*global console, document, navigator, setTimeout, window */

/**
 * Split {@code prettyPrint} into multiple timeouts so as not to interfere with
 * UI events.
 * If set to {@code false}, {@code prettyPrint()} is synchronous.
 */
var PR_SHOULD_USE_CONTINUATION = true;

/** the number of characters between tab columns */
var PR_TAB_WIDTH = 8;

/** Walks the DOM returning a properly escaped version of innerHTML.
  * @param {Node} node
  * @param {Array.<string>} out output buffer that receives chunks of HTML.
  */
var PR_normalizedHtml;

/** Contains functions for creating and registering new language handlers.
  * @type {Object}
  */
var PR;

/** Pretty print a chunk of code.
  *
  * @param {string} sourceCodeHtml code as html
  * @return {string} code as html, but prettier
  */
var prettyPrintOne;
/** find all the < pre > and < code > tags in the DOM with class=prettyprint
  * and prettify them.
  * @param {Function} opt_whenDone if specified, called when the last entry
  *     has been finished.
  */
var prettyPrint;

/** browser detection. @extern */
function _pr_isIE6() {
  var isIE6 = navigator && navigator.userAgent &&
      /\bMSIE 6\./.test(navigator.userAgent);
  _pr_isIE6 = function () { return isIE6; };
  return isIE6;
}


(function () {
  /** Splits input on space and returns an Object mapping each non-empty part to
    * true.
    */
  function wordSet(words) {
    words = words.split(/ /g);
    var set = {};
    for (var i = words.length; --i >= 0;) {
      var w = words[i];
      if (w) { set[w] = null; }
    }
    return set;
  }

  // Keyword lists for various languages.
  var FLOW_CONTROL_KEYWORDS =
      "break continue do else for if return while ";
  var C_KEYWORDS = FLOW_CONTROL_KEYWORDS + "auto case char const default " +
      "double enum extern float goto int long register short signed sizeof " +
      "static struct switch typedef union unsigned void volatile ";
  var COMMON_KEYWORDS = C_KEYWORDS + "catch class delete false import " +
      "new operator private protected public this throw true try ";
  var CPP_KEYWORDS = COMMON_KEYWORDS + "alignof align_union asm axiom bool " +
      "concept concept_map const_cast constexpr decltype " +
      "dynamic_cast explicit export friend inline late_check " +
      "mutable namespace nullptr reinterpret_cast static_assert static_cast " +
      "template typeid typename typeof using virtual wchar_t where ";
  var JAVA_KEYWORDS = COMMON_KEYWORDS +
      "boolean byte extends final finally implements import instanceof null " +
      "native package strictfp super synchronized throws transient ";
  var CSHARP_KEYWORDS = JAVA_KEYWORDS +
      "as base by checked decimal delegate descending event " +
      "fixed foreach from group implicit in interface internal into is lock " +
      "object out override orderby params readonly ref sbyte sealed " +
      "stackalloc string select uint ulong unchecked unsafe ushort var ";
  var JSCRIPT_KEYWORDS = COMMON_KEYWORDS +
      "debugger eval export function get null set undefined var with " +
      "Infinity NaN ";
  var PERL_KEYWORDS = "caller delete die do dump elsif eval exit foreach for " +
      "goto if import last local my next no our print package redo require " +
      "sub undef unless until use wantarray while BEGIN END ";
  var PYTHON_KEYWORDS = FLOW_CONTROL_KEYWORDS + "and as assert class def del " +
      "elif except exec finally from global import in is lambda " +
      "nonlocal not or pass print raise try with yield " +
      "False True None ";
  var RUBY_KEYWORDS = FLOW_CONTROL_KEYWORDS + "alias and begin case class def" +
      " defined elsif end ensure false in module next nil not or redo rescue " +
      "retry self super then true undef unless until when yield BEGIN END ";
  var SH_KEYWORDS = FLOW_CONTROL_KEYWORDS + "case done elif esac eval fi " +
      "function in local set then until ";
  var ALL_KEYWORDS = (
      CPP_KEYWORDS + CSHARP_KEYWORDS + JSCRIPT_KEYWORDS + PERL_KEYWORDS +
      PYTHON_KEYWORDS + RUBY_KEYWORDS + SH_KEYWORDS);

  // token style names.  correspond to css classes
  /** token style for a string literal */
  var PR_STRING = 'str';
  /** token style for a keyword */
  var PR_KEYWORD = 'kwd';
  /** token style for a comment */
  var PR_COMMENT = 'com';
  /** token style for a type */
  var PR_TYPE = 'typ';
  /** token style for a literal value.  e.g. 1, null, true. */
  var PR_LITERAL = 'lit';
  /** token style for a punctuation string. */
  var PR_PUNCTUATION = 'pun';
  /** token style for a punctuation string. */
  var PR_PLAIN = 'pln';

  /** token style for an sgml tag. */
  var PR_TAG = 'tag';
  /** token style for a markup declaration such as a DOCTYPE. */
  var PR_DECLARATION = 'dec';
  /** token style for embedded source. */
  var PR_SOURCE = 'src';
  /** token style for an sgml attribute name. */
  var PR_ATTRIB_NAME = 'atn';
  /** token style for an sgml attribute value. */
  var PR_ATTRIB_VALUE = 'atv';

  /**
   * A class that indicates a section of markup that is not code, e.g. to allow
   * embedding of line numbers within code listings.
   */
  var PR_NOCODE = 'nocode';

  function isWordChar(ch) {
    return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z');
  }

  /** Splice one array into another.
    * Like the python <code>
    * container[containerPosition:containerPosition + countReplaced] = inserted
    * </code>
    * @param {Array} inserted
    * @param {Array} container modified in place
    * @param {Number} containerPosition
    * @param {Number} countReplaced
    */
  function spliceArrayInto(
      inserted, container, containerPosition, countReplaced) {
    inserted.unshift(containerPosition, countReplaced || 0);
    try {
      container.splice.apply(container, inserted);
    } finally {
      inserted.splice(0, 2);
    }
  }

  /** A set of tokens that can precede a regular expression literal in
    * javascript.
    * http://www.mozilla.org/js/language/js20/rationale/syntax.html has the full
    * list, but I've removed ones that might be problematic when seen in
    * languages that don't support regular expression literals.
    *
    * <p>Specifically, I've removed any keywords that can't precede a regexp
    * literal in a syntactically legal javascript program, and I've removed the
    * "in" keyword since it's not a keyword in many languages, and might be used
    * as a count of inches.
    * @private
    */
  var REGEXP_PRECEDER_PATTERN = function () {
      var preceders = [
          "!", "!=", "!==", "#", "%", "%=", "&", "&&", "&&=",
          "&=", "(", "*", "*=", /* "+", */ "+=", ",", /* "-", */ "-=",
          "->", /*".", "..", "...", handled below */ "/", "/=", ":", "::", ";",
          "<", "<<", "<<=", "<=", "=", "==", "===", ">",
          ">=", ">>", ">>=", ">>>", ">>>=", "?", "@", "[",
          "^", "^=", "^^", "^^=", "{", "|", "|=", "||",
          "||=", "~" /* handles =~ and !~ */,
          "break", "case", "continue", "delete",
          "do", "else", "finally", "instanceof",
          "return", "throw", "try", "typeof"
          ];
      var pattern = '(?:' +
          '(?:(?:^|[^0-9.])\\.{1,3})|' +  // a dot that's not part of a number
          '(?:(?:^|[^\\+])\\+)|' +  // allow + but not ++
          '(?:(?:^|[^\\-])-)';  // allow - but not --
      for (var i = 0; i < preceders.length; ++i) {
        var preceder = preceders[i];
        if (isWordChar(preceder.charAt(0))) {
          pattern += '|\\b' + preceder;
        } else {
          pattern += '|' + preceder.replace(/([^=<>:&])/g, '\\$1');
        }
      }
      pattern += '|^)\\s*$';  // matches at end, and matches empty string
      return new RegExp(pattern);
      // CAVEAT: this does not properly handle the case where a regular
      // expression immediately follows another since a regular expression may
      // have flags for case-sensitivity and the like.  Having regexp tokens
      // adjacent is not
      // valid in any language I'm aware of, so I'm punting.
      // TODO: maybe style special characters inside a regexp as punctuation.
    }();

  // Define regexps here so that the interpreter doesn't have to create an
  // object each time the function containing them is called.
  // The language spec requires a new object created even if you don't access
  // the $1 members.
  var pr_amp = /&/g;
  var pr_lt = /</g;
  var pr_gt = />/g;
  var pr_quot = /\"/g;
  /** like textToHtml but escapes double quotes to be attribute safe. */
  function attribToHtml(str) {
    return str.replace(pr_amp, '&amp;')
        .replace(pr_lt, '&lt;')
        .replace(pr_gt, '&gt;')
        .replace(pr_quot, '&quot;');
  }

  /** escapest html special characters to html. */
  function textToHtml(str) {
    return str.replace(pr_amp, '&amp;')
        .replace(pr_lt, '&lt;')
        .replace(pr_gt, '&gt;');
  }


  var pr_ltEnt = /&lt;/g;
  var pr_gtEnt = /&gt;/g;
  var pr_aposEnt = /&apos;/g;
  var pr_quotEnt = /&quot;/g;
  var pr_ampEnt = /&amp;/g;
  var pr_nbspEnt = /&nbsp;/g;
  /** unescapes html to plain text. */
  function htmlToText(html) {
    var pos = html.indexOf('&');
    if (pos < 0) { return html; }
    // Handle numeric entities specially.  We can't use functional substitution
    // since that doesn't work in older versions of Safari.
    // These should be rare since most browsers convert them to normal chars.
    for (--pos; (pos = html.indexOf('&#', pos + 1)) >= 0;) {
      var end = html.indexOf(';', pos);
      if (end >= 0) {
        var num = html.substring(pos + 3, end);
        var radix = 10;
        if (num && num.charAt(0) === 'x') {
          num = num.substring(1);
          radix = 16;
        }
        var codePoint = parseInt(num, radix);
        if (!isNaN(codePoint)) {
          html = (html.substring(0, pos) + String.fromCharCode(codePoint) +
                  html.substring(end + 1));
        }
      }
    }

    return html.replace(pr_ltEnt, '<')
        .replace(pr_gtEnt, '>')
        .replace(pr_aposEnt, "'")
        .replace(pr_quotEnt, '"')
        .replace(pr_ampEnt, '&')
        .replace(pr_nbspEnt, ' ');
  }

  /** is the given node's innerHTML normally unescaped? */
  function isRawContent(node) {
    return 'XMP' === node.tagName;
  }

  function normalizedHtml(node, out) {
    switch (node.nodeType) {
      case 1:  // an element
        var name = node.tagName.toLowerCase();
        out.push('<', name);
        for (var i = 0; i < node.attributes.length; ++i) {
          var attr = node.attributes[i];
          if (!attr.specified) { continue; }
          out.push(' ');
          normalizedHtml(attr, out);
        }
        out.push('>');
        for (var child = node.firstChild; child; child = child.nextSibling) {
          normalizedHtml(child, out);
        }
        if (node.firstChild || !/^(?:br|link|img)$/.test(name)) {
          out.push('<\/', name, '>');
        }
        break;
      case 2: // an attribute
        out.push(node.name.toLowerCase(), '="', attribToHtml(node.value), '"');
        break;
      case 3: case 4: // text
        out.push(textToHtml(node.nodeValue));
        break;
    }
  }

  var PR_innerHtmlWorks = null;
  function getInnerHtml(node) {
    // inner html is hopelessly broken in Safari 2.0.4 when the content is
    // an html description of well formed XML and the containing tag is a PRE
    // tag, so we detect that case and emulate innerHTML.
    if (null === PR_innerHtmlWorks) {
      var testNode = document.createElement('PRE');
      testNode.appendChild(
          document.createTextNode('<!DOCTYPE foo PUBLIC "foo bar">\n<foo />'));
      PR_innerHtmlWorks = !/</.test(testNode.innerHTML);
    }

    if (PR_innerHtmlWorks) {
      var content = node.innerHTML;
      // XMP tags contain unescaped entities so require special handling.
      if (isRawContent(node)) {
        content = textToHtml(content);
      }
      return content;
    }

    var out = [];
    for (var child = node.firstChild; child; child = child.nextSibling) {
      normalizedHtml(child, out);
    }
    return out.join('');
  }

  /** returns a function that expand tabs to spaces.  This function can be fed
    * successive chunks of text, and will maintain its own internal state to
    * keep track of how tabs are expanded.
    * @return {function (string) : string} a function that takes
    *   plain text and return the text with tabs expanded.
    * @private
    */
  function makeTabExpander(tabWidth) {
    var SPACES = '                ';
    var charInLine = 0;

    return function (plainText) {
      // walk over each character looking for tabs and newlines.
      // On tabs, expand them.  On newlines, reset charInLine.
      // Otherwise increment charInLine
      var out = null;
      var pos = 0;
      for (var i = 0, n = plainText.length; i < n; ++i) {
        var ch = plainText.charAt(i);

        switch (ch) {
          case '\t':
            if (!out) { out = []; }
            out.push(plainText.substring(pos, i));
            // calculate how much space we need in front of this part
            // nSpaces is the amount of padding -- the number of spaces needed
            // to move us to the next column, where columns occur at factors of
            // tabWidth.
            var nSpaces = tabWidth - (charInLine % tabWidth);
            charInLine += nSpaces;
            for (; nSpaces >= 0; nSpaces -= SPACES.length) {
              out.push(SPACES.substring(0, nSpaces));
            }
            pos = i + 1;
            break;
          case '\n':
            charInLine = 0;
            break;
          default:
            ++charInLine;
        }
      }
      if (!out) { return plainText; }
      out.push(plainText.substring(pos));
      return out.join('');
    };
  }

  // The below pattern matches one of the following
  // (1) /[^<]+/ : A run of characters other than '<'
  // (2) /<!--.*?-->/: an HTML comment
  // (3) /<!\[CDATA\[.*?\]\]>/: a cdata section
  // (3) /<\/?[a-zA-Z][^>]*>/ : A probably tag that should not be highlighted
  // (4) /</ : A '<' that does not begin a larger chunk.  Treated as 1
  var pr_chunkPattern =
  /(?:[^<]+|<!--[\s\S]*?-->|<!\[CDATA\[([\s\S]*?)\]\]>|<\/?[a-zA-Z][^>]*>|<)/g;
  var pr_commentPrefix = /^<!--/;
  var pr_cdataPrefix = /^<\[CDATA\[/;
  var pr_brPrefix = /^<br\b/i;
  var pr_tagNameRe = /^<(\/?)([a-zA-Z]+)/;

  /** split markup into chunks of html tags (style null) and
    * plain text (style {@link #PR_PLAIN}), converting tags which are
    * significant for tokenization (<br>) into their textual equivalent.
    *
    * @param {string} s html where whitespace is considered significant.
    * @return {Object} source code and extracted tags.
    * @private
    */
  function extractTags(s) {
    // since the pattern has the 'g' modifier and defines no capturing groups,
    // this will return a list of all chunks which we then classify and wrap as
    // PR_Tokens
    var matches = s.match(pr_chunkPattern);
    var sourceBuf = [];
    var sourceBufLen = 0;
    var extractedTags = [];
    if (matches) {
      for (var i = 0, n = matches.length; i < n; ++i) {
        var match = matches[i];
        if (match.length > 1 && match.charAt(0) === '<') {
          if (pr_commentPrefix.test(match)) { continue; }
          if (pr_cdataPrefix.test(match)) {
            // strip CDATA prefix and suffix.  Don't unescape since it's CDATA
            sourceBuf.push(match.substring(9, match.length - 3));
            sourceBufLen += match.length - 12;
          } else if (pr_brPrefix.test(match)) {
            // <br> tags are lexically significant so convert them to text.
            // This is undone later.
            sourceBuf.push('\n');
            ++sourceBufLen;
          } else {
            if (match.indexOf(PR_NOCODE) >= 0 && isNoCodeTag(match)) {
              // A <span class="nocode"> will start a section that should be
              // ignored.  Continue walking the list until we see a matching end
              // tag.
              var name = match.match(pr_tagNameRe)[2];
              var depth = 1;
              end_tag_loop:
              for (var j = i + 1; j < n; ++j) {
                var name2 = matches[j].match(pr_tagNameRe);
                if (name2 && name2[2] === name) {
                  if (name2[1] === '/') {
                    if (--depth === 0) { break end_tag_loop; }
                  } else {
                    ++depth;
                  }
                }
              }
              if (j < n) {
                extractedTags.push(
                    sourceBufLen, matches.slice(i, j + 1).join(''));
                i = j;
              } else {  // Ignore unclosed sections.
                extractedTags.push(sourceBufLen, match);
              }
            } else {
              extractedTags.push(sourceBufLen, match);
            }
          }
        } else {
          var literalText = htmlToText(match);
          sourceBuf.push(literalText);
          sourceBufLen += literalText.length;
        }
      }
    }
    return { source: sourceBuf.join(''), tags: extractedTags };
  }

  /** True if the given tag contains a class attribute with the nocode class. */
  function isNoCodeTag(tag) {
    return !!tag
        // First canonicalize the representation of attributes
        .replace(/\s(\w+)\s*=\s*(?:\"([^\"]*)\"|'([^\']*)'|(\S+))/g,
                 ' $1="$2$3$4"')
        // Then look for the attribute we want.
        .match(/[cC][lL][aA][sS][sS]=\"[^\"]*\bnocode\b/);
  }

  /** Given triples of [style, pattern, context] returns a lexing function,
    * The lexing function interprets the patterns to find token boundaries and
    * returns a decoration list of the form
    * [index_0, style_0, index_1, style_1, ..., index_n, style_n]
    * where index_n is an index into the sourceCode, and style_n is a style
    * constant like PR_PLAIN.  index_n-1 <= index_n, and style_n-1 applies to
    * all characters in sourceCode[index_n-1:index_n].
    *
    * The stylePatterns is a list whose elements have the form
    * [style : string, pattern : RegExp, context : RegExp, shortcut : string].
    &
    * Style is a style constant like PR_PLAIN.
    *
    * Pattern must only match prefixes, and if it matches a prefix and context
    * is null or matches the last non-comment token parsed, then that match is
    * considered a token with the same style.
    *
    * Context is applied to the last non-whitespace, non-comment token
    * recognized.
    *
    * Shortcut is an optional string of characters, any of which, if the first
    * character, gurantee that this pattern and only this pattern matches.
    *
    * @param {Array} shortcutStylePatterns patterns that always start with
    *   a known character.  Must have a shortcut string.
    * @param {Array} fallthroughStylePatterns patterns that will be tried in
    *   order if the shortcut ones fail.  May have shortcuts.
    *
    * @return {function (string, number?) : Array.<number|string>} a
    *   function that takes source code and returns a list of decorations.
    */
  function createSimpleLexer(shortcutStylePatterns,
                             fallthroughStylePatterns) {
    var shortcuts = {};
    (function () {
      var allPatterns = shortcutStylePatterns.concat(fallthroughStylePatterns);
      for (var i = allPatterns.length; --i >= 0;) {
        var patternParts = allPatterns[i];
        var shortcutChars = patternParts[3];
        if (shortcutChars) {
          for (var c = shortcutChars.length; --c >= 0;) {
            shortcuts[shortcutChars.charAt(c)] = patternParts;
          }
        }
      }
    })();

    var nPatterns = fallthroughStylePatterns.length;
    var notWs = /\S/;

    return function (sourceCode, opt_basePos) {
      opt_basePos = opt_basePos || 0;
      var decorations = [opt_basePos, PR_PLAIN];
      var lastToken = '';
      var pos = 0;  // index into sourceCode
      var tail = sourceCode;

      while (tail.length) {
        var style;
        var token = null;
        var match;

        var patternParts = shortcuts[tail.charAt(0)];
        if (patternParts) {
          match = tail.match(patternParts[1]);
          token = match[0];
          style = patternParts[0];
        } else {
          for (var i = 0; i < nPatterns; ++i) {
            patternParts = fallthroughStylePatterns[i];
            var contextPattern = patternParts[2];
            if (contextPattern && !contextPattern.test(lastToken)) {
              // rule can't be used
              continue;
            }
            match = tail.match(patternParts[1]);
            if (match) {
              token = match[0];
              style = patternParts[0];
              break;
            }
          }

          if (!token) {  // make sure that we make progress
            style = PR_PLAIN;
            token = tail.substring(0, 1);
          }
        }

        decorations.push(opt_basePos + pos, style);
        pos += token.length;
        tail = tail.substring(token.length);
        if (style !== PR_COMMENT && notWs.test(token)) { lastToken = token; }
      }
      return decorations;
    };
  }

  var PR_MARKUP_LEXER = createSimpleLexer([], [
      [PR_PLAIN,       /^[^<]+/, null],
      [PR_DECLARATION, /^<!\w[^>]*(?:>|$)/, null],
      [PR_COMMENT,     /^<!--[\s\S]*?(?:-->|$)/, null],
      [PR_SOURCE,      /^<\?[\s\S]*?(?:\?>|$)/, null],
      [PR_SOURCE,      /^<%[\s\S]*?(?:%>|$)/, null],
      [PR_SOURCE,
       // Tags whose content is not escaped, and which contain source code.
       /^<(script|style|xmp)\b[^>]*>[\s\S]*?<\/\1\b[^>]*>/i, null],
      [PR_TAG,         /^<\/?\w[^<>]*>/, null]
      ]);
  // Splits any of the source|style|xmp entries above into a start tag,
  // source content, and end tag.
  var PR_SOURCE_CHUNK_PARTS = /^(<[^>]*>)([\s\S]*)(<\/[^>]*>)$/;
  /** split markup on tags, comments, application directives, and other top
    * level constructs.  Tags are returned as a single token - attributes are
    * not yet broken out.
    * @private
    */
  function tokenizeMarkup(source) {
    var decorations = PR_MARKUP_LEXER(source);
    for (var i = 0; i < decorations.length; i += 2) {
      if (decorations[i + 1] === PR_SOURCE) {
        var start, end;
        start = decorations[i];
        end = i + 2 < decorations.length ? decorations[i + 2] : source.length;
        // Split out start and end script tags as actual tags, and leave the
        // body with style SCRIPT.
        var sourceChunk = source.substring(start, end);
        var match = sourceChunk.match(PR_SOURCE_CHUNK_PARTS);
        if (match) {
          decorations.splice(
              i, 2,
              start, PR_TAG,  // the open chunk
              start + match[1].length, PR_SOURCE,
              start + match[1].length + (match[2] || '').length, PR_TAG);
        }
      }
    }
    return decorations;
  }

  var PR_TAG_LEXER = createSimpleLexer([
      [PR_ATTRIB_VALUE, /^\'[^\']*(?:\'|$)/, null, "'"],
      [PR_ATTRIB_VALUE, /^\"[^\"]*(?:\"|$)/, null, '"'],
      [PR_PUNCTUATION,  /^[<>\/=]+/, null, '<>/=']
      ], [
      [PR_TAG,          /^[\w:\-]+/, /^</],
      [PR_ATTRIB_VALUE, /^[\w\-]+/, /^=/],
      [PR_ATTRIB_NAME,  /^[\w:\-]+/, null],
      [PR_PLAIN,        /^\s+/, null, ' \t\r\n']
      ]);
  /** split tags attributes and their values out from the tag name, and
    * recursively lex source chunks.
    * @private
    */
  function splitTagAttributes(source, decorations) {
    for (var i = 0; i < decorations.length; i += 2) {
      var style = decorations[i + 1];
      if (style === PR_TAG) {
        var start, end;
        start = decorations[i];
        end = i + 2 < decorations.length ? decorations[i + 2] : source.length;
        var chunk = source.substring(start, end);
        var subDecorations = PR_TAG_LEXER(chunk, start);
        spliceArrayInto(subDecorations, decorations, i, 2);
        i += subDecorations.length - 2;
      }
    }
    return decorations;
  }

  /** returns a function that produces a list of decorations from source text.
    *
    * This code treats ", ', and ` as string delimiters, and \ as a string
    * escape.  It does not recognize perl's qq() style strings.
    * It has no special handling for double delimiter escapes as in basic, or
    * the tripled delimiters used in python, but should work on those regardless
    * although in those cases a single string literal may be broken up into
    * multiple adjacent string literals.
    *
    * It recognizes C, C++, and shell style comments.
    *
    * @param {Object} options a set of optional parameters.
    * @return {function (string) : Array.<string|number>} a
    *     decorator that takes sourceCode as plain text and that returns a
    *     decoration list
    */
  function sourceDecorator(options) {
    var shortcutStylePatterns = [], fallthroughStylePatterns = [];
    if (options.tripleQuotedStrings) {
      // '''multi-line-string''', 'single-line-string', and double-quoted
      shortcutStylePatterns.push(
          [PR_STRING,  /^(?:\'\'\'(?:[^\'\\]|\\[\s\S]|\'{1,2}(?=[^\']))*(?:\'\'\'|$)|\"\"\"(?:[^\"\\]|\\[\s\S]|\"{1,2}(?=[^\"]))*(?:\"\"\"|$)|\'(?:[^\\\']|\\[\s\S])*(?:\'|$)|\"(?:[^\\\"]|\\[\s\S])*(?:\"|$))/,
           null, '\'"']);
    } else if (options.multiLineStrings) {
      // 'multi-line-string', "multi-line-string"
      shortcutStylePatterns.push(
          [PR_STRING,  /^(?:\'(?:[^\\\']|\\[\s\S])*(?:\'|$)|\"(?:[^\\\"]|\\[\s\S])*(?:\"|$)|\`(?:[^\\\`]|\\[\s\S])*(?:\`|$))/,
           null, '\'"`']);
    } else {
      // 'single-line-string', "single-line-string"
      shortcutStylePatterns.push(
          [PR_STRING,
           /^(?:\'(?:[^\\\'\r\n]|\\.)*(?:\'|$)|\"(?:[^\\\"\r\n]|\\.)*(?:\"|$))/,
           null, '"\'']);
    }
    fallthroughStylePatterns.push(
        [PR_PLAIN,   /^(?:[^\'\"\`\/\#]+)/, null, ' \r\n']);
    if (options.hashComments) {
      shortcutStylePatterns.push([PR_COMMENT, /^#[^\r\n]*/, null, '#']);
    }
    if (options.cStyleComments) {
      fallthroughStylePatterns.push([PR_COMMENT, /^\/\/[^\r\n]*/, null]);
      fallthroughStylePatterns.push(
          [PR_COMMENT, /^\/\*[\s\S]*?(?:\*\/|$)/, null]);
    }
    if (options.regexLiterals) {
      var REGEX_LITERAL = (
          // A regular expression literal starts with a slash that is
          // not followed by * or / so that it is not confused with
          // comments.
          '^/(?=[^/*])'
          // and then contains any number of raw characters,
          + '(?:[^/\\x5B\\x5C]'
          // escape sequences (\x5C),
          +    '|\\x5C[\\s\\S]'
          // or non-nesting character sets (\x5B\x5D);
          +    '|\\x5B(?:[^\\x5C\\x5D]|\\x5C[\\s\\S])*(?:\\x5D|$))+'
          // finally closed by a /.
          + '(?:/|$)');
      fallthroughStylePatterns.push(
          [PR_STRING, new RegExp(REGEX_LITERAL), REGEXP_PRECEDER_PATTERN]);
    }

    var keywords = wordSet(options.keywords);

    options = null;

    /** splits the given string into comment, string, and "other" tokens.
      * @param {string} sourceCode as plain text
      * @return {Array.<number|string>} a decoration list.
      * @private
      */
    var splitStringAndCommentTokens = createSimpleLexer(
        shortcutStylePatterns, fallthroughStylePatterns);

    var styleLiteralIdentifierPuncRecognizer = createSimpleLexer([], [
        [PR_PLAIN,       /^\s+/, null, ' \r\n'],
        // TODO(mikesamuel): recognize non-latin letters and numerals in idents
        [PR_PLAIN,       /^[a-z_$@][a-z_$@0-9]*/i, null],
        // A hex number
        [PR_LITERAL,     /^0x[a-f0-9]+[a-z]/i, null],
        // An octal or decimal number, possibly in scientific notation
        [PR_LITERAL,
         /^(?:\d(?:_\d+)*\d*(?:\.\d*)?|\.\d+)(?:e[+\-]?\d+)?[a-z]*/i,
         null, '123456789'],
        [PR_PUNCTUATION, /^[^\s\w\.$@]+/, null]
        // Fallback will handle decimal points not adjacent to a digit
      ]);

    /** splits plain text tokens into more specific tokens, and then tries to
      * recognize keywords, and types.
      * @private
      */
    function splitNonStringNonCommentTokens(source, decorations) {
      for (var i = 0; i < decorations.length; i += 2) {
        var style = decorations[i + 1];
        if (style === PR_PLAIN) {
          var start, end, chunk, subDecs;
          start = decorations[i];
          end = i + 2 < decorations.length ? decorations[i + 2] : source.length;
          chunk = source.substring(start, end);
          subDecs = styleLiteralIdentifierPuncRecognizer(chunk, start);
          for (var j = 0, m = subDecs.length; j < m; j += 2) {
            var subStyle = subDecs[j + 1];
            if (subStyle === PR_PLAIN) {
              var subStart = subDecs[j];
              var subEnd = j + 2 < m ? subDecs[j + 2] : chunk.length;
              var token = source.substring(subStart, subEnd);
              if (token === '.') {
                subDecs[j + 1] = PR_PUNCTUATION;
              } else if (token in keywords) {
                subDecs[j + 1] = PR_KEYWORD;
              } else if (/^@?[A-Z][A-Z$]*[a-z][A-Za-z$]*$/.test(token)) {
                // classify types and annotations using Java's style conventions
                subDecs[j + 1] = token.charAt(0) === '@' ? PR_LITERAL : PR_TYPE;
              }
            }
          }
          spliceArrayInto(subDecs, decorations, i, 2);
          i += subDecs.length - 2;
        }
      }
      return decorations;
    }

    return function (sourceCode) {
      // Split into strings, comments, and other.
      // We do this because strings and comments are easily recognizable and can
      // contain stuff that looks like other tokens, so we want to mark those
      // early so we don't recurse into them.
      var decorations = splitStringAndCommentTokens(sourceCode);

      // Split non comment|string tokens on whitespace and word boundaries
      decorations = splitNonStringNonCommentTokens(sourceCode, decorations);

      return decorations;
    };
  }

  var decorateSource = sourceDecorator({
        keywords: ALL_KEYWORDS,
        hashComments: true,
        cStyleComments: true,
        multiLineStrings: true,
        regexLiterals: true
      });

  /** identify regions of markup that are really source code, and recursivley
    * lex them.
    * @private
    */
  function splitSourceNodes(source, decorations) {
    for (var i = 0; i < decorations.length; i += 2) {
      var style = decorations[i + 1];
      if (style === PR_SOURCE) {
        // Recurse using the non-markup lexer
        var start, end;
        start = decorations[i];
        end = i + 2 < decorations.length ? decorations[i + 2] : source.length;
        var subDecorations = decorateSource(source.substring(start, end));
        for (var j = 0, m = subDecorations.length; j < m; j += 2) {
          subDecorations[j] += start;
        }
        spliceArrayInto(subDecorations, decorations, i, 2);
        i += subDecorations.length - 2;
      }
    }
    return decorations;
  }

  /** identify attribute values that really contain source code and recursively
    * lex them.
    * @private
    */
  function splitSourceAttributes(source, decorations) {
    var nextValueIsSource = false;
    for (var i = 0; i < decorations.length; i += 2) {
      var style = decorations[i + 1];
      var start, end;
      if (style === PR_ATTRIB_NAME) {
        start = decorations[i];
        end = i + 2 < decorations.length ? decorations[i + 2] : source.length;
        nextValueIsSource = /^on|^style$/i.test(source.substring(start, end));
      } else if (style === PR_ATTRIB_VALUE) {
        if (nextValueIsSource) {
          start = decorations[i];
          end = i + 2 < decorations.length ? decorations[i + 2] : source.length;
          var attribValue = source.substring(start, end);
          var attribLen = attribValue.length;
          var quoted =
              (attribLen >= 2 && /^[\"\']/.test(attribValue) &&
               attribValue.charAt(0) === attribValue.charAt(attribLen - 1));

          var attribSource;
          var attribSourceStart;
          var attribSourceEnd;
          if (quoted) {
            attribSourceStart = start + 1;
            attribSourceEnd = end - 1;
            attribSource = attribValue;
          } else {
            attribSourceStart = start + 1;
            attribSourceEnd = end - 1;
            attribSource = attribValue.substring(1, attribValue.length - 1);
          }

          var attribSourceDecorations = decorateSource(attribSource);
          for (var j = 0, m = attribSourceDecorations.length; j < m; j += 2) {
            attribSourceDecorations[j] += attribSourceStart;
          }

          if (quoted) {
            attribSourceDecorations.push(attribSourceEnd, PR_ATTRIB_VALUE);
            spliceArrayInto(attribSourceDecorations, decorations, i + 2, 0);
          } else {
            spliceArrayInto(attribSourceDecorations, decorations, i, 2);
          }
        }
        nextValueIsSource = false;
      }
    }
    return decorations;
  }

  /** returns a decoration list given a string of markup.
    *
    * This code recognizes a number of constructs.
    * <!-- ... --> comment
    * <!\w ... >   declaration
    * <\w ... >    tag
    * </\w ... >   tag
    * <?...?>      embedded source
    * <%...%>      embedded source
    * &[#\w]...;   entity
    *
    * It does not recognizes %foo; doctype entities from  .
    *
    * It will recurse into any <style>, <script>, and on* attributes using
    * PR_lexSource.
    */
  function decorateMarkup(sourceCode) {
    // This function works as follows:
    // 1) Start by splitting the markup into text and tag chunks
    //    Input:  string s
    //    Output: List<PR_Token> where style in (PR_PLAIN, null)
    // 2) Then split the text chunks further into comments, declarations,
    //    tags, etc.
    //    After each split, consider whether the token is the start of an
    //    embedded source section, i.e. is an open <script> tag.  If it is, find
    //    the corresponding close token, and don't bother to lex in between.
    //    Input:  List<string>
    //    Output: List<PR_Token> with style in
    //            (PR_TAG, PR_PLAIN, PR_SOURCE, null)
    // 3) Finally go over each tag token and split out attribute names and
    //    values.
    //    Input:  List<PR_Token>
    //    Output: List<PR_Token> where style in
    //            (PR_TAG, PR_PLAIN, PR_SOURCE, NAME, VALUE, null)
    var decorations = tokenizeMarkup(sourceCode);
    decorations = splitTagAttributes(sourceCode, decorations);
    decorations = splitSourceNodes(sourceCode, decorations);
    decorations = splitSourceAttributes(sourceCode, decorations);
    return decorations;
  }

  /**
    * @param {string} sourceText plain text
    * @param {Array.<number|string>} extractedTags chunks of raw html preceded
    *   by their position in sourceText in order.
    * @param {Array.<number|string>} decorations style classes preceded by their
    *   position in sourceText in order.
    * @return {string} html
    * @private
    */
  function recombineTagsAndDecorations(sourceText, extractedTags, decorations) {
    var html = [];
    // index past the last char in sourceText written to html
    var outputIdx = 0;

    var openDecoration = null;
    var currentDecoration = null;
    var tagPos = 0;  // index into extractedTags
    var decPos = 0;  // index into decorations
    var tabExpander = makeTabExpander(PR_TAB_WIDTH);

    var adjacentSpaceRe = /([\r\n ]) /g;
    var startOrSpaceRe = /(^| ) /gm;
    var newlineRe = /\r\n?|\n/g;
    var trailingSpaceRe = /[ \r\n]$/;
    var lastWasSpace = true;  // the last text chunk emitted ended with a space.
    
    // A helper function that is responsible for opening sections of decoration
    // and outputing properly escaped chunks of source
    function emitTextUpTo(sourceIdx) {
      if (sourceIdx > outputIdx) {
        if (openDecoration && openDecoration !== currentDecoration) {
          // Close the current decoration
          html.push('</span>');
          openDecoration = null;
        }
        if (!openDecoration && currentDecoration) {
          openDecoration = currentDecoration;
          html.push('<span class="', openDecoration, '">');
        }
        // This interacts badly with some wikis which introduces paragraph tags
        // into pre blocks for some strange reason.
        // It's necessary for IE though which seems to lose the preformattedness
        // of <pre> tags when their innerHTML is assigned.
        // http://stud3.tuwien.ac.at/~e0226430/innerHtmlQuirk.html
        // and it serves to undo the conversion of <br>s to newlines done in
        // chunkify.
        var htmlChunk = textToHtml(
            tabExpander(sourceText.substring(outputIdx, sourceIdx)))
            .replace(lastWasSpace
                     ? startOrSpaceRe
                     : adjacentSpaceRe, '$1&nbsp;');
        // Keep track of whether we need to escape space at the beginning of the
        // next chunk.
        lastWasSpace = trailingSpaceRe.test(htmlChunk);
        html.push(htmlChunk.replace(newlineRe, '<br />'));
        outputIdx = sourceIdx;
      }
    }

    while (true) {
      // Determine if we're going to consume a tag this time around.  Otherwise
      // we consume a decoration or exit.
      var outputTag;
      if (tagPos < extractedTags.length) {
        if (decPos < decorations.length) {
          // Pick one giving preference to extractedTags since we shouldn't open
          // a new style that we're going to have to immediately close in order
          // to output a tag.
          outputTag = extractedTags[tagPos] <= decorations[decPos];
        } else {
          outputTag = true;
        }
      } else {
        outputTag = false;
      }
      // Consume either a decoration or a tag or exit.
      if (outputTag) {
        emitTextUpTo(extractedTags[tagPos]);
        if (openDecoration) {
          // Close the current decoration
          html.push('</span>');
          openDecoration = null;
        }
        html.push(extractedTags[tagPos + 1]);
        tagPos += 2;
      } else if (decPos < decorations.length) {
        emitTextUpTo(decorations[decPos]);
        currentDecoration = decorations[decPos + 1];
        decPos += 2;
      } else {
        break;
      }
    }
    emitTextUpTo(sourceText.length);
    if (openDecoration) {
      html.push('</span>');
    }

    return html.join('');
  }

  /** Maps language-specific file extensions to handlers. */
  var langHandlerRegistry = {};
  /** Register a language handler for the given file extensions.
    * @param {function (string) : Array.<number|string>} handler
    *     a function from source code to a list of decorations.
    * @param {Array.<string>} fileExtensions
    */
  function registerLangHandler(handler, fileExtensions) {
    for (var i = fileExtensions.length; --i >= 0;) {
      var ext = fileExtensions[i];
      if (!langHandlerRegistry.hasOwnProperty(ext)) {
        langHandlerRegistry[ext] = handler;
      } else if ('console' in window) {
        console.log('cannot override language handler %s', ext);
      }
    }
  }
  registerLangHandler(decorateSource, ['default-code']);
  registerLangHandler(decorateMarkup,
                      ['default-markup', 'html', 'htm', 'xhtml', 'xml', 'xsl']);
  registerLangHandler(sourceDecorator({
          keywords: CPP_KEYWORDS,
          hashComments: true,
          cStyleComments: true
        }), ['c', 'cc', 'cpp', 'cxx', 'cyc']);
  registerLangHandler(sourceDecorator({
          keywords: CSHARP_KEYWORDS,
          hashComments: true,
          cStyleComments: true
        }), ['cs']);
  registerLangHandler(sourceDecorator({
          keywords: JAVA_KEYWORDS,
          cStyleComments: true
        }), ['java']);
  registerLangHandler(sourceDecorator({
          keywords: SH_KEYWORDS,
          hashComments: true,
          multiLineStrings: true
        }), ['bsh', 'csh', 'sh']);
  registerLangHandler(sourceDecorator({
          keywords: PYTHON_KEYWORDS,
          hashComments: true,
          multiLineStrings: true,
          tripleQuotedStrings: true
        }), ['cv', 'py']);
  registerLangHandler(sourceDecorator({
          keywords: PERL_KEYWORDS,
          hashComments: true,
          multiLineStrings: true,
          regexLiterals: true
        }), ['perl', 'pl', 'pm']);
  registerLangHandler(sourceDecorator({
          keywords: RUBY_KEYWORDS,
          hashComments: true,
          multiLineStrings: true,
          regexLiterals: true
        }), ['rb']);
  registerLangHandler(sourceDecorator({
          keywords: JSCRIPT_KEYWORDS,
          cStyleComments: true,
          regexLiterals: true
        }), ['js']);

  function prettyPrintOne(sourceCodeHtml, opt_langExtension) {
    try {
      // Extract tags, and convert the source code to plain text.
      var sourceAndExtractedTags = extractTags(sourceCodeHtml);
      /** Plain text. @type {string} */
      var source = sourceAndExtractedTags.source;

      /** Even entries are positions in source in ascending order.  Odd entries
        * are tags that were extracted at that position.
        * @type {Array.<number|string>}
        */
      var extractedTags = sourceAndExtractedTags.tags;

      // Pick a lexer and apply it.
      if (!langHandlerRegistry.hasOwnProperty(opt_langExtension)) {
        // Treat it as markup if the first non whitespace character is a < and
        // the last non-whitespace character is a >.
        opt_langExtension =
            /^\s*</.test(source) ? 'default-markup' : 'default-code';
      }

      /** Even entries are positions in source in ascending order.  Odd enties
        * are style markers (e.g., PR_COMMENT) that run from that position until
        * the end.
        * @type {Array.<number|string>}
        */
      var decorations = langHandlerRegistry[opt_langExtension].call({}, source);

      // Integrate the decorations and tags back into the source code to produce
      // a decorated html string.
      return recombineTagsAndDecorations(source, extractedTags, decorations);
    } catch (e) {
      if ('console' in window) {
        console.log(e);
        console.trace();
      }
      return sourceCodeHtml;
    }
  }

  function prettyPrint(opt_whenDone) {
    var isIE6 = _pr_isIE6();

    // fetch a list of nodes to rewrite
    var codeSegments = [
        document.getElementsByTagName('pre'),
        document.getElementsByTagName('code'),
        document.getElementsByTagName('xmp') ];
    var elements = [];
    for (var i = 0; i < codeSegments.length; ++i) {
      for (var j = 0; j < codeSegments[i].length; ++j) {
        elements.push(codeSegments[i][j]);
      }
    }
    codeSegments = null;

    // the loop is broken into a series of continuations to make sure that we
    // don't make the browser unresponsive when rewriting a large page.
    var k = 0;

    function doWork() {
      var endTime = (PR_SHOULD_USE_CONTINUATION ?
                     new Date().getTime() + 250 /* ms */ :
                     Infinity);
      for (; k < elements.length && new Date().getTime() < endTime; k++) {
        var cs = elements[k];
        if (cs.className && cs.className.indexOf('prettyprint') >= 0) {
          // If the classes includes a language extensions, use it.
          // Language extensions can be specified like
          //     <pre class="prettyprint lang-cpp">
          // the language extension "cpp" is used to find a language handler as
          // passed to PR_registerLangHandler.
          var langExtension = cs.className.match(/\blang-(\w+)\b/);
          if (langExtension) { langExtension = langExtension[1]; }

          // make sure this is not nested in an already prettified element
          var nested = false;
          for (var p = cs.parentNode; p; p = p.parentNode) {
            if ((p.tagName === 'pre' || p.tagName === 'code' ||
                 p.tagName === 'xmp') &&
                p.className && p.className.indexOf('prettyprint') >= 0) {
              nested = true;
              break;
            }
          }
          if (!nested) {
            // fetch the content as a snippet of properly escaped HTML.
            // Firefox adds newlines at the end.
            var content = getInnerHtml(cs);
            content = content.replace(/(?:\r\n?|\n)$/, '');

            // do the pretty printing
            var newContent = prettyPrintOne(content, langExtension);

            // push the prettified html back into the tag.
            if (!isRawContent(cs)) {
              // just replace the old html with the new
              cs.innerHTML = newContent;
            } else {
              // we need to change the tag to a <pre> since <xmp>s do not allow
              // embedded tags such as the span tags used to attach styles to
              // sections of source code.
              var pre = document.createElement('PRE');
              for (var i = 0; i < cs.attributes.length; ++i) {
                var a = cs.attributes[i];
                if (a.specified) {
                  var aname = a.name.toLowerCase();
                  if (aname === 'class') {
                    pre.className = a.value;  // For IE 6
                  } else {
                    pre.setAttribute(a.name, a.value);
                  }
                }
              }
              pre.innerHTML = newContent;

              // remove the old
              cs.parentNode.replaceChild(pre, cs);
              cs = pre;
            }

            // Replace <br>s with line-feeds so that copying and pasting works
            // on IE 6.
            // Doing this on other browsers breaks lots of stuff since \r\n is
            // treated as two newlines on Firefox, and doing this also slows
            // down rendering.
            if (isIE6 && cs.tagName === 'PRE') {
              var lineBreaks = cs.getElementsByTagName('br');
              for (var j = lineBreaks.length; --j >= 0;) {
                var lineBreak = lineBreaks[j];
                lineBreak.parentNode.replaceChild(
                    document.createTextNode('\r\n'), lineBreak);
              }
            }
          }
        }
      }
      if (k < elements.length) {
        // finish up in a continuation
        setTimeout(doWork, 250);
      } else if (opt_whenDone) {
        opt_whenDone();
      }
    }

    doWork();
  }

  window['PR_normalizedHtml'] = normalizedHtml;
  window['prettyPrintOne'] = prettyPrintOne;
  window['prettyPrint'] = prettyPrint;
  window['PR'] = {
        'createSimpleLexer': createSimpleLexer,
        'registerLangHandler': registerLangHandler,
        'sourceDecorator': sourceDecorator,
        'PR_ATTRIB_NAME': PR_ATTRIB_NAME,
        'PR_ATTRIB_VALUE': PR_ATTRIB_VALUE,
        'PR_COMMENT': PR_COMMENT,
        'PR_DECLARATION': PR_DECLARATION,
        'PR_KEYWORD': PR_KEYWORD,
        'PR_LITERAL': PR_LITERAL,
        'PR_NOCODE': PR_NOCODE,
        'PR_PLAIN': PR_PLAIN,
        'PR_PUNCTUATION': PR_PUNCTUATION,
        'PR_SOURCE': PR_SOURCE,
        'PR_STRING': PR_STRING,
        'PR_TAG': PR_TAG,
        'PR_TYPE': PR_TYPE
      };
})();
