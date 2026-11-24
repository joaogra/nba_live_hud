export function formatNbaClock(isoClock: string): string {
  const match = isoClock.match(/PT(\d+)M([\d.]+)S/);
  if (!match) return "12:00";

  const minutes = parseInt(match[1], 10);
  const seconds = Math.floor(parseFloat(match[2]));

  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function formatPeriod(period: number): string {
  if (period <= 4) return `Q${period}`;
  const otNumber = period - 4;
  return otNumber === 1 ? "OT" : `${otNumber}OT`;
}