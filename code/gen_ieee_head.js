const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Footer,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, SectionType,
} = require("docx");

const FONT = "Times New Roman";
const BODY = 20;   // 10 pt
const SMALL = 16;  // 8 pt
const COLW = 5040, FULLW = 10440;

const ROM = ["","I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX"];
const secTok = (tok) => { const m = tok.match(/^(\d+)(?:\.(\d+))?$/); const a = ROM[+m[1]]; return m[2] ? a + "-" + String.fromCharCode(64 + +m[2]) : a; };
function xref(t) {
  t = t.replace(/\b(Sections?) (\d+(?:\.\d+)?(?:(?:, and |, | and | to | or )(?:\d+\.\d+|[1-7](?![\d.]| seed| run| setting| arm| attack)))*)/g,
    (m, w, list) => w + " " + list.replace(/\d+(?:\.\d+)?/g, secTok));
  t = t.replace(/\b(Tables?) (\d+(?:(?:, and |, | and | to | or )\d+(?![\d.]| seed| run| setting| arm| attack))*)/g,
    (m, w, list) => w + " " + list.replace(/\d+/g, (d) => ROM[+d]));
  return t.replace(/\bFigures\b/g, "Figs.").replace(/\bFigure\b/g, "Fig.");
}

function runs(text, size = BODY, extra = {}, raw = false) {
  if (!raw) text = xref(text);
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, size, ...extra }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, font: FONT, size, ...extra }));
    else out.push(new TextRun({ text: tok.slice(1, -1), italics: true, font: FONT, size, ...extra }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, size, ...extra }));
  return out;
}
const P = (text, opts = {}) => new Paragraph({
  children: runs(text), alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 80, line: 240 }, indent: { firstLine: 240 }, ...opts,
});
const H1 = (text) => {
  const m = text.match(/^(\d+)\. (.*)$/);
  const label = m ? ROM[+m[1]] + ". " + m[2] : text;
  return new Paragraph({
    heading: HeadingLevel.HEADING_1, keepNext: true, alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 },
    children: [new TextRun({ text: label, font: FONT, size: 20, smallCaps: true })],
  });
};
const H2 = (text) => {
  const m = text.match(/^(\d+)\.(\d+) (.*)$/);
  const label = String.fromCharCode(64 + +m[2]) + ". " + m[3];
  return new Paragraph({
    heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 120, after: 60 },
    children: [new TextRun({ text: label, italics: true, font: FONT, size: 20 })],
  });
};
const caption = (text, keepNext = false) => {
  const m = text.match(/^\*\*(Table|Figure) (\d+)\.\*\* ?([\s\S]*)$/);
  const arr = [];
  if (m[1] === "Table") {
    arr.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 100, after: 20 },
      children: [new TextRun({ text: "TABLE " + ROM[+m[2]], font: FONT, size: SMALL })] }));
    arr.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, keepNext: true, spacing: { after: 60 }, children: runs(m[3], SMALL) }));
  } else {
    arr.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { before: 40, after: 120 },
      children: [new TextRun({ text: "Fig. " + m[2] + ". ", font: FONT, size: SMALL, bold: true }), ...runs(m[3], SMALL)] }));
  }
  return arr;
};
const REF = (text) => {
  const m = text.match(/^\[(\d+)\] ([\s\S]*)$/);
  return new Paragraph({
    children: [new TextRun({ text: "[" + m[1] + "]\t", font: FONT, size: SMALL }), ...runs(m[2], SMALL, {}, true)],
    alignment: AlignmentType.JUSTIFIED, spacing: { after: 40 },
    indent: { left: 360, hanging: 360 }, tabStops: [{ type: "left", position: 360 }],
  });
};

const border = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, header, rows) {
  const maxCell = Math.max(...rows.map(r => Math.max(...r.map(c => c.length))));
  const span = header.length >= 5 || (header.length === 4 && maxCell > 28) || (header.length === 3 && maxCell > 150);
  const target = span ? FULLW : COLW;
  const sum = widths.reduce((a, b) => a + b, 0);
  const w2 = widths.map(w => Math.round(w * target / sum));
  w2[w2.length - 1] += target - w2.reduce((a, b) => a + b, 0);
  const mk = (txt, w, isHead, kn) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA },
    shading: isHead ? { fill: "E3E8EE", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 30, bottom: 30, left: 60, right: 60 },
    children: [new Paragraph({ keepNext: kn, children: runs(txt, SMALL, isHead ? { bold: true } : {}), spacing: { after: 0 } })],
  });
  const t = new Table({
    width: { size: target, type: WidthType.DXA }, columnWidths: w2,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: header.map((h, i) => mk(h, w2[i], true, true)) }),
      ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => mk(c, w2[i], false, span && ri < rows.length - 1)) })),
    ],
  });
  t.__span = span; t.__table = true;
  console.log("table", header.length, "cols", maxCell, "maxcell", span ? "SPAN" : "column");
  return t;
}
const gap = () => { const p = new Paragraph({ children: [], spacing: { after: 40 } }); p.__gap = true; return p; };
function pngSize(file) { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
const IMG = (file, w, id, desc) => {
  const path = "/mnt/user-data/outputs/paper/figures/" + file;
  const [pw, ph] = pngSize(path);
  const p = new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 80, after: 40 }, keepNext: true,
    children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: w, height: Math.round(w * ph / pw) },
      altText: { title: id, description: desc, name: id } })] });
  p.__span = true; p.__fig = true;
  return p;
};

const body = [];
const A = AlignmentType.CENTER;
const titleBlock = [
  new Paragraph({ alignment: A, spacing: { after: 160 },
    children: [new TextRun({ text: "An Exploratory Feature-Space Comparison of One-Time and Incremental Adversarial Updates for Network Intrusion Detection", font: FONT, size: 44 })] }),
  new Paragraph({ alignment: A, spacing: { after: 20 }, children: [new TextRun({ text: "Ajay Kumar", font: FONT, size: 22 })] }),
  new Paragraph({ alignment: A, spacing: { after: 0 }, children: [new TextRun({ text: "Dept. of Computer Science and Engineering", italics: true, font: FONT, size: 20 })] }),
  new Paragraph({ alignment: A, spacing: { after: 0 }, children: [new TextRun({ text: "SRM Institute of Science and Technology", italics: true, font: FONT, size: 20 })] }),
  new Paragraph({ alignment: A, spacing: { after: 0 }, children: [new TextRun({ text: "India", italics: true, font: FONT, size: 20 })] }),
  new Paragraph({ alignment: A, spacing: { after: 200 }, children: [new TextRun({ text: "ajay.kumar.leo10@gmail.com", font: FONT, size: 20 })] }),
];
