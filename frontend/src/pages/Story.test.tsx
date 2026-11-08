import { describe, expect, it } from 'vitest';
import { PHONE_DRAWING_FLOOR, anchorInDrawing, storyStageFloor } from './Story';

describe('the story stage maps a callout anchor into the drawing under the measured band', () => {
  it('keeps the anchor before the band is measured', () => {
    expect(anchorInDrawing({ x: 0.55, y: 0.2 }, 0, 620)).toEqual({ x: 0.55, y: 0.2 });
    expect(anchorInDrawing({ x: 0.55, y: 0.2 }, 180, 0)).toEqual({ x: 0.55, y: 0.2 });
  });

  it('puts the top of the drawing at the bottom of the band and keeps x', () => {
    expect(anchorInDrawing({ x: 0.3, y: 0 }, 200, 620)).toEqual({ x: 0.3, y: 200 / 620 });
    expect(anchorInDrawing({ x: 0.3, y: 1 }, 200, 620).y).toBeCloseTo(1, 12);
  });

  it('never lands an anchor inside the band, whatever its fraction', () => {
    for (const band of [86, 130, 212, 300]) for (const y of [0, 0.05, 0.2, 0.5, 0.86]) {
      expect(anchorInDrawing({ x: 0.5, y }, band, 620).y * 620).toBeGreaterThanOrEqual(band);
    }
  });

  it('leaves the anchor alone when the band would take the whole stage', () => {
    expect(anchorInDrawing({ x: 0.5, y: 0.4 }, 700, 620)).toEqual({ x: 0.5, y: 0.4 });
  });

  it('adversarial: an anchor read as a fraction of the whole stage falls under a card; mapped into the drawing it never does', () => {
    // the 0.15.006 candidate: the infected peak at y 0.2 of a 620 px phone stage, under a 212 px band of two card rows
    const stage = 620, band = 212, anchor = { x: 0.55, y: 0.2 };
    expect(anchor.y * stage).toBeLessThan(band);
    expect(anchorInDrawing(anchor, band, stage).y * stage).toBeGreaterThanOrEqual(band);
  });
});

describe('the phone stage floor follows the measured band', () => {
  it('is 620 px before the band is measured and keeps the drawing floor under any band', () => {
    expect(storyStageFloor(0)).toBe(620);
    for (const band of [120, 212, 286, 380]) expect(storyStageFloor(band) - band).toBeGreaterThanOrEqual(PHONE_DRAWING_FLOOR);
  });

  it('stays within the shell bounds of 300 to 900 px', () => {
    expect(storyStageFloor(600)).toBe(900);
    expect(Number.isInteger(storyStageFloor(212.4))).toBe(true);
  });
});
