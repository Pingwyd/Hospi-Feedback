import { useCallback, type KeyboardEvent } from "react";

type ComposeEnterToSendTarget = HTMLTextAreaElement | HTMLInputElement;

type UseComposeEnterToSendOptions = {
  /** Same gate the Send button uses (non-empty, not busy, etc.). */
  canSend: boolean;
  onSend: () => void;
};

/**
 * Enter sends; Shift+Enter keeps default newline behavior (textarea only).
 * Ignores IME composition Enter.
 */
export function useComposeEnterToSend({
  canSend,
  onSend,
}: UseComposeEnterToSendOptions) {
  return useCallback(
    (event: KeyboardEvent<ComposeEnterToSendTarget>) => {
      if (event.key !== "Enter" || event.nativeEvent.isComposing) {
        return;
      }
      if (event.shiftKey) {
        return;
      }
      event.preventDefault();
      if (!canSend) {
        return;
      }
      onSend();
    },
    [canSend, onSend],
  );
}
