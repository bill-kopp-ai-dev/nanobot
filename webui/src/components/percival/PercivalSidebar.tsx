// PERCIVAL: wrapper da Sidebar original do upstream.
// Decisão G2-AltB (2026-08-01): composição por fora, SEM patch em Sidebar.tsx.
// Decisão B2 (revisada): link KG renderizado como irmão, abaixo do footer.
// Decisão B4: ícone Lucide-react (Network ou Share2).
// Decisão B2: Settings continua visível e funcional (esconder está em suspenso).
// Extensibilidade: futuros botões no rodapé (mesmo padrão) entram como
// irmãos do <a> KG abaixo — sem patch em Sidebar.tsx.
import { Network } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Sidebar as UpstreamSidebar } from "@/components/Sidebar";
import { resolveKgInterfaceUrl } from "@/lib/kg-interface";

export function PercivalSidebar(
  props: React.ComponentProps<typeof UpstreamSidebar>,
) {
  const { t } = useTranslation();
  const kgUrl = resolveKgInterfaceUrl();

  return (
    <>
      <UpstreamSidebar {...props} />
      {/* PERCIVAL: link Knowledge Graph no rodapé (B2 revisada, G2-AltB). */}
      <a
        href={kgUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={t("sidebar.knowledgeGraph")}
      >
        <Network className="h-4 w-4" />
        <span>{t("sidebar.knowledgeGraph")}</span>
      </a>
    </>
  );
}
