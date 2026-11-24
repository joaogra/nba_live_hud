export interface TeamBrand {
  primary: string;
  secondary: string;
}

export const NBA_TEAM_COLORS: Record<string, TeamBrand> = {
  ATL: { primary: "#E03A3E", secondary: "#C1D32F" },
  BKN: { primary: "#000000", secondary: "#FFFFFF" },
  BOS: { primary: "#007A33", secondary: "#BA9653" },
  CHA: { primary: "#1D1160", secondary: "#00788C" },
  CHI: { primary: "#CE1141", secondary: "#000000" },
  CLE: { primary: "#860038", secondary: "#FDBB30" },
  DAL: { primary: "#00538C", secondary: "#B8C4CA" },
  DEN: { primary: "#0E2240", secondary: "#FEC524" },
  DET: { primary: "#C8102E", secondary: "#1D42BA" },
  GSW: { primary: "#1D428A", secondary: "#FFC72C" },
  HOU: { primary: "#CE1141", secondary: "#000000" },
  IND: { primary: "#002D62", secondary: "#FDBB30" },
  LAC: { primary: "#C8102E", secondary: "#1D428A" },
  LAL: { primary: "#552583", secondary: "#FDB927" },
  MEM: { primary: "#5D76A9", secondary: "#12173F" },
  MIA: { primary: "#98002E", secondary: "#F9A01B" },
  MIL: { primary: "#00471B", secondary: "#EEE1C6" },
  MIN: { primary: "#0C2340", secondary: "#236192" },
  NOP: { primary: "#0C2340", secondary: "#C8102E" },
  NYK: { primary: "#006BB6", secondary: "#F58426" },
  OKC: { primary: "#007AC1", secondary: "#EF3B24" },
  ORL: { primary: "#0077C0", secondary: "#C4CED4" },
  PHI: { primary: "#006BB6", secondary: "#ED174C" },
  PHX: { primary: "#1D1160", secondary: "#E56020" },
  POR: { primary: "#E03A3E", secondary: "#000000" },
  SAC: { primary: "#5A2D81", secondary: "#63727A" },
  SAS: { primary: "#C4CED4", secondary: "#000000" },
  TOR: { primary: "#CE1141", secondary: "#000000" },
  UTA: { primary: "#002B5C", secondary: "#F9A01B" },
  WAS: { primary: "#002B5C", secondary: "#E31837" },
  DEFAULT: { primary: "#1E293B", secondary: "#94A3B8" },
};

export function getTeamColors(tricode: string): TeamBrand {
  return NBA_TEAM_COLORS[tricode.toUpperCase()] ?? NBA_TEAM_COLORS.DEFAULT;
}

export interface EventVisualStyle {
  label: string;
  accentClass: string;
  badgeBgClass: string;
}

export const EVENT_STYLES: Record<string, EventVisualStyle> = {
  "3pt": { label: "3 PONTOS", accentClass: "border-amber-400", badgeBgClass: "bg-amber-500 text-slate-950" },
  "2pt": { label: "CESTA", accentClass: "border-emerald-400", badgeBgClass: "bg-emerald-500 text-slate-950" },
  freethrow: { label: "LANCE LIVRE", accentClass: "border-sky-400", badgeBgClass: "bg-sky-500 text-slate-950" },
  foul: { label: "FALTA", accentClass: "border-rose-500", badgeBgClass: "bg-rose-600 text-white" },
  substitution: { label: "SUBSTITUIÇÃO", accentClass: "border-indigo-400", badgeBgClass: "bg-indigo-500 text-white" },
  turnover: { label: "TURNOVER", accentClass: "border-orange-500", badgeBgClass: "bg-orange-500 text-slate-950" },
  block: { label: "TOCO", accentClass: "border-purple-400", badgeBgClass: "bg-purple-500 text-white" },
  steal: { label: "ROUBO DE BOLA", accentClass: "border-teal-400", badgeBgClass: "bg-teal-500 text-slate-950" },
};