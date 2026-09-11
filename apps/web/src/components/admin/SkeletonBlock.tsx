type SkeletonBlockProps = {
  className?: string;
};

export function SkeletonBlock({ className = "h-4 w-full" }: SkeletonBlockProps) {
  return <div className={`skeleton-shimmer rounded-md ${className}`} aria-hidden />;
}

export function SkeletonCard() {
  return (
    <div className="space-y-3 rounded-2xl border border-ink/10 bg-white/60 p-6 shadow-sm">
      <SkeletonBlock className="h-6 w-1/3" />
      <SkeletonBlock className="h-4 w-full" />
      <SkeletonBlock className="h-4 w-5/6" />
      <SkeletonBlock className="h-4 w-2/3" />
    </div>
  );
}
