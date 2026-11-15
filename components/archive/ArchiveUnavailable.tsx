import Notice from "@/components/ui/Notice";
import { ARCHIVE_COPY } from "@/lib/copy/archive";

/** The index is missing or not valid: a neutral notice, not an error and not a blank page. */
export default function ArchiveUnavailable() {
  return (
    <main className="mx-auto max-w-[1184px] px-space-4 pt-space-5 pb-space-7 bp-lg:px-space-6 bp-lg:pt-space-7">
      <h1 className="m-0 mb-space-4 font-display text-display-md text-ink bp-lg:text-display-lg">{ARCHIVE_COPY.title}</h1>
      <Notice>{ARCHIVE_COPY.unavailable}</Notice>
    </main>
  );
}
