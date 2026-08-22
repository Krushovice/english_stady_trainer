import { describe, expect, it } from "vitest";
import { formatClock, formatWhen } from "./ExamPage";

describe("formatClock", () => {
  it("formats whole minutes with a zero-padded seconds field", () => {
    expect(formatClock(600)).toBe("10:00");
  });

  it("pads single-digit seconds", () => {
    expect(formatClock(65)).toBe("1:05");
  });

  it("formats sub-minute durations without a leading zero on minutes", () => {
    expect(formatClock(9)).toBe("0:09");
  });

  it("clamps negative durations to zero instead of showing a negative clock", () => {
    expect(formatClock(-5)).toBe("0:00");
  });

  it("treats exactly zero as zero", () => {
    expect(formatClock(0)).toBe("0:00");
  });
});

describe("formatWhen", () => {
  it("produces a non-empty locale string for a valid ISO timestamp", () => {
    const result = formatWhen("2026-08-22T10:30:00Z");
    expect(result.length).toBeGreaterThan(0);
    expect(result).not.toBe("Invalid Date");
  });
});
