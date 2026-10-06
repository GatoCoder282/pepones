import { getContent } from "@/lib/content";
import { Home } from "@/components/Home";

export default function Page() {
  return <Home content={getContent()} />;
}
