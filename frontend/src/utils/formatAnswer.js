/**
 * Wrap inline `code` and obvious code lines in monospace spans for multilingual answers.
 */
export function formatAnswerText(text) {
  if (!text) return [];

  const parts = text.split(/(`[^`]+`)/g);

  return parts.map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return { type: "code", value: part.slice(1, -1), key: `code-${index}` };
    }
    return { type: "text", value: part, key: `text-${index}` };
  });
}
