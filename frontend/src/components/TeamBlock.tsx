import { getTeamColors } from "../config/theme";

interface TeamBlockProps {
  tricode: string;
  teamName: string;
  record: string;
  score: number;
  align: "left" | "right";
}

export function TeamBlock({
  tricode,
  teamName,
  record,
  score,
  align,
}: TeamBlockProps) {
  const colors = getTeamColors(tricode);
  const isRight = align === "right";

  return (
    <div
      className={`flex items-center gap-4 px-4 py-2.5 ${
        isRight ? "flex-row-reverse text-right" : "flex-row text-left"
      }`}
    >
      {/* Faixa vertical com a cor primária da franquia */}
      <div
        className="h-11 w-1.5 rounded-full shrink-0"
        style={{ backgroundColor: colors.primary }}
      />

      {/* Sigla, nome e campanha (record) */}
      <div className="min-w-[84px]">
        <div className="flex items-baseline gap-1.5 justify-between">
          <span className="text-xl font-black tracking-tight text-white">
            {tricode}
          </span>
          {record && (
            <span className="text-[11px] font-medium text-slate-400">
              ({record})
            </span>
          )}
        </div>
        {teamName && (
          <p className="text-xs font-medium text-slate-400 truncate max-w-[100px]">
            {teamName}
          </p>
        )}
      </div>

      {/* Pontuação com largura tabular (evita o placar "pular" quando os números mudam) */}
      <div className="text-3xl font-black tabular-nums tracking-tight text-white">
        {score}
      </div>
    </div>
  );
}