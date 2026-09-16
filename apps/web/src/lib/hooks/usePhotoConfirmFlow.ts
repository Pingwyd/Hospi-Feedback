"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { filterValidReportImageFiles } from "@/lib/attachments/constants";

export type PhotoConfirmItem = {
  id: string;
  file: File;
  previewUrl: string;
};

type UsePhotoConfirmFlowOptions = {
  disabled?: boolean;
  onConfirm: (files: File[]) => void | Promise<void>;
  onValidationErrors?: (messages: string[]) => void;
};

function createConfirmItem(file: File, index: number): PhotoConfirmItem {
  return {
    id: `${file.name}-${file.lastModified}-${file.size}-${index}-${Math.random().toString(36).slice(2, 9)}`,
    file,
    previewUrl: URL.createObjectURL(file),
  };
}

export function usePhotoConfirmFlow({
  disabled = false,
  onConfirm,
  onValidationErrors,
}: UsePhotoConfirmFlowOptions) {
  const [modalOpen, setModalOpen] = useState(false);
  const [pendingItems, setPendingItems] = useState<PhotoConfirmItem[]>([]);
  const [confirming, setConfirming] = useState(false);
  const uploadLockedRef = useRef(false);
  const pendingItemsRef = useRef<PhotoConfirmItem[]>([]);

  useEffect(() => {
    pendingItemsRef.current = pendingItems;
  }, [pendingItems]);

  const revokeItems = useCallback((items: PhotoConfirmItem[]) => {
    for (const item of items) {
      URL.revokeObjectURL(item.previewUrl);
    }
  }, []);

  const closeModal = useCallback(() => {
    setPendingItems((current) => {
      revokeItems(current);
      return [];
    });
    setModalOpen(false);
  }, [revokeItems]);

  const appendFiles = useCallback(
    (files: File[]) => {
      if (disabled || uploadLockedRef.current || confirming || files.length === 0) {
        return;
      }
      const { valid, errors } = filterValidReportImageFiles(files);
      if (errors.length > 0) {
        onValidationErrors?.(errors);
      }
      if (valid.length === 0) {
        return;
      }
      const newItems = valid.map((file, index) => createConfirmItem(file, index));
      setPendingItems((current) => {
        const merged = [...current, ...newItems];
        return merged;
      });
      setModalOpen(true);
    },
    [confirming, disabled, onValidationErrors],
  );

  const removePendingItem = useCallback(
    (id: string) => {
      if (uploadLockedRef.current || confirming) {
        return;
      }
      setPendingItems((current) => {
        const target = current.find((entry) => entry.id === id);
        if (target) {
          URL.revokeObjectURL(target.previewUrl);
        }
        const next = current.filter((entry) => entry.id !== id);
        if (next.length === 0) {
          setModalOpen(false);
        }
        return next;
      });
    },
    [confirming],
  );

  const handleConfirm = useCallback(async () => {
    if (uploadLockedRef.current || confirming || pendingItems.length === 0) {
      return;
    }
    uploadLockedRef.current = true;
    setConfirming(true);
    const files = pendingItems.map((item) => item.file);
    try {
      await onConfirm(files);
      revokeItems(pendingItems);
      setPendingItems([]);
      setModalOpen(false);
    } catch {
      // Keep the modal open so the reporter can retry or discard.
    } finally {
      uploadLockedRef.current = false;
      setConfirming(false);
    }
  }, [confirming, onConfirm, pendingItems, revokeItems]);

  const handleCancel = useCallback(() => {
    if (uploadLockedRef.current || confirming) {
      return;
    }
    closeModal();
  }, [closeModal, confirming]);

  useEffect(() => {
    return () => {
      revokeItems(pendingItemsRef.current);
    };
  }, [revokeItems]);

  return {
    modalOpen,
    pendingItems,
    confirming,
    uploadLockedRef,
    enqueueFiles: appendFiles,
    removePendingItem,
    handleConfirm,
    handleCancel,
    isBusy: confirming || uploadLockedRef.current,
  };
}
