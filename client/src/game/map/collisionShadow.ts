export class CollisionShadow {
  constructor(
    private solids: boolean[][],
    public tileW: number,
    public tileH: number
  ) {}

  inBoundsPx(px: number, py: number) {
    return (
      py >= 0 &&
      px >= 0 &&
      py < this.solids.length * this.tileH &&
      px < this.solids[0].length * this.tileW
    );
  }

  isSolidPx(px: number, py: number) {
    const tx = Math.floor(px / this.tileW);
    const ty = Math.floor(py / this.tileH);
    if (
      ty < 0 ||
      tx < 0 ||
      ty >= this.solids.length ||
      tx >= this.solids[0].length
    )
      return true;
    return !!this.solids[ty][tx];
  }

  blockedAABB(px: number, py: number, w: number, h: number) {
    const pts: Array<[number, number]> = [
      [px, py],
      [px + w, py],
      [px, py + h],
      [px + w, py + h],
    ];
    return pts.some(([x, y]) => this.isSolidPx(x, y));
  }
}

