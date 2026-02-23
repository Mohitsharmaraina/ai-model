// import ReactMarkdown from "react-markdown";
// import remarkMath from "remark-math";
// import remarkGfm from "remark-gfm";
// import rehypeKatex from "rehype-katex";
// import "katex/dist/katex.min.css"; // Don't forget this!

// const MessageRenderer = ({ content }) => {
//   return (
//     <div
//       className="prose dark:prose-invert prose-sm max-w-none
//                  prose-p:leading-relaxed prose-pre:bg-gray-200
//                  dark:prose-pre:bg-gray-700 prose-li:my-1"
//     >
//       <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
//         {content}
//       </ReactMarkdown>
//     </div>
//   );
// };

// export default MessageRenderer;

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

// 1. This function fixes the AI's "broken" math formatting
const preprocessLaTeX = (content) => {
  if (!content) return "";
  return (
    content
      // Convert \[ math \] or [ math ] to $$ math $$ (Block Math)
      .replace(/\\\[/g, "$$$$")
      .replace(/\\\]/g, "$$$$")
      .replace(/(^|\s)\[\s/g, "$1$$$$ ") // Handles [ at start of line
      .replace(/\s\](\s|$)/g, " $$$$$1") // Handles ] at end of line

      // Convert \( math \) or ( math ) to $ math $ (Inline Math)
      .replace(/\\\( /g, "$")
      .replace(/ \\\)/g, "$")
      // Be careful with simple parentheses: only convert if they contain a backslash (LaTeX symbol)
      .replace(/\((\\.*)\)/g, "$$$1$")
  );
};

const MessageRenderer = ({ content }) => {
  const processedContent = preprocessLaTeX(content);

  return (
    <div
      className="prose dark:prose-invert prose-sm max-w-none 
                    prose-p:leading-relaxed prose-pre:bg-gray-200 
                    dark:prose-pre:bg-gray-700 prose-li:my-1
                    break-words overflow-x-auto"
    >
      <ReactMarkdown
        remarkPlugins={[remarkMath, remarkGfm]}
        rehypePlugins={[rehypeKatex]}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};
export default MessageRenderer;
