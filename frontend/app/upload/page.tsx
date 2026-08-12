import type { Metadata } from "next";
import { UploadClient } from "./upload-client";

export const metadata: Metadata = {
  title: "Upload",
  description: "Score one or more résumés against every open role in the corpus.",
};

export default function UploadPage() {
  return <UploadClient />;
}
