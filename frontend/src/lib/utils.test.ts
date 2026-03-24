import { describe, it, expect } from "vitest";
import { formatBytes, formatDate } from "./utils";

describe("Utility Functions", () => {
  describe("formatBytes", () => {
    it("formats 0 bytes correctly", () => {
      expect(formatBytes(0)).toBe("0 Bytes");
    });

    it("formats KB correctly", () => {
      expect(formatBytes(1024)).toBe("1 KB");
      expect(formatBytes(1500)).toBe("1.46 KB");
    });

    it("formats MB correctly", () => {
      expect(formatBytes(1048576)).toBe("1 MB");
      expect(formatBytes(5000000)).toBe("4.77 MB");
    });
    
    it("handles explicit decimals argument", () => {
      expect(formatBytes(1500, 0)).toBe("1 KB");
      expect(formatBytes(1500, 3)).toBe("1.465 KB");
    });
  });

  describe("formatDate", () => {
    it("formats a standard ISO string", () => {
      const dateStr = "2024-03-24T12:00:00Z";
      const result = formatDate(dateStr);
      // Depending on local timezone, this will format differently, 
      // but should be a valid string not "Invalid Date"
      expect(result).not.toBe("Invalid Date");
      expect(typeof result).toBe("string");
    });
  });
});
