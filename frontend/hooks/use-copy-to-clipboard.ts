import { useCallback, useState } from "react";

export const useCopyToClipboard = (resetDelay = 2000): [boolean, (text: string) => void] => {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(
    (text: string) => {
      navigator.clipboard.writeText(text).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), resetDelay);
      });
    },
    [resetDelay]
  );

  return [copied, copy];
};
