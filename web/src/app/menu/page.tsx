import { getContent } from "@/lib/content";
import { MenuPage } from "@/components/MenuPage";
export const metadata = { title: "El menú" };
export default function Page() {
  return <MenuPage content={getContent()} />;
}
