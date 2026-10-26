
const flat = [];
body.forEach(it => { if (Array.isArray(it)) it.forEach(x => { x.__cap = true; flat.push(x); }); else flat.push(it); });
for (let i = 0; i < flat.length; i++) {
  if (flat[i].__table && flat[i].__span) {
    let j = i - 1; while (j >= 0 && flat[j].__cap) { flat[j].__span = true; j--; }
    if (flat[i + 1] && flat[i + 1].__gap) flat[i + 1].__span = true;
  }
  if (flat[i].__fig && flat[i + 1] && flat[i + 1].__cap) flat[i + 1].__span = true;
}
const groups = [{ span: true, children: titleBlock }];
flat.forEach(it => {
  const s = !!it.__span;
  const g = groups[groups.length - 1];
  if (g.span === s) g.children.push(it); else groups.push({ span: s, children: [it] });
});
const pageProps = { size: { width: 12240, height: 15840 }, margin: { top: 1080, right: 900, bottom: 1300, left: 900, footer: 600 } };
const sections = groups.map((g, k) => ({
  properties: { type: k === 0 ? undefined : SectionType.CONTINUOUS, page: pageProps, column: { count: g.span ? 1 : 2, space: 360 } },
  footers: k === 0 ? { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] }) } : undefined,
  children: g.children,
}));
const doc = new Document({
  creator: "Ajay Kumar", title: "An Exploratory Feature-Space Comparison of One-Time and Incremental Adversarial Updates for Network Intrusion Detection",
  styles: {
    default: { document: { run: { font: FONT, size: BODY } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 20, font: FONT, smallCaps: true }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 20, italics: true, font: FONT }, paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 1 } },
    ],
  },
  sections,
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync("/mnt/user-data/outputs/paper/NIDS_IEEE_Paper_v13.docx", buf); console.log("written", groups.length, "sections"); });
