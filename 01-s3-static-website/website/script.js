const letters = [
  ["ა","ან","ატამი"],["ბ","ბან","ბავშვი"],["გ","განი","გული"],["დ","დონი","დედა"],
  ["ე","ენი","ეზო"],["ვ","ვინი","ვაშლი"],["ზ","ზენი","ზღვა"],["თ","თანი","თოვლი"],
  ["ი","ინი","ია"],["კ","კანი","კალამი"],["ლ","ლასი","ლომი"],["მ","მანი","მზე"],
  ["ნ","ნარი","ნავი"],["ო","ონი","ოქრო"],["პ","პარი","პური"],["ჟ","ჟანი","ჟირაფი"],
  ["რ","რაე","რძე"],["ს","სანი","სახლი"],["ტ","ტარი","ტყე"],["უ","უნი","უბანი"],
  ["ფ","ფარი","ფანჯარა"],["ქ","ქანი","ქალაქი"],["ღ","ღანი","ღრუბელი"],["ყ","ყარი","ყვავილი"],
  ["შ","შინი","შაქარი"],["ჩ","ჩინი","ჩიტი"],["ც","ცანი","ცა"],["ძ","ძილი","ძმა"],
  ["წ","წილი","წიგნი"],["ჭ","ჭარი","ჭიქა"],["ხ","ხანი","ხე"],["ჯ","ჯანი","ჯადოქარი"],
  ["ჰ","ჰაე","ჰაერი"]
];

const grid = document.getElementById("grid");

function select(index) {
  const [ch, name, word] = letters[index];
  document.getElementById("detailLetter").textContent = ch;
  document.getElementById("detailName").textContent = name;
  document.getElementById("detailWord").textContent = word;
  document.getElementById("detailPos").textContent = `${index + 1} / ${letters.length}`;
  document.getElementById("heroLetter").textContent = ch;
  grid.querySelectorAll("button").forEach((b, i) => b.setAttribute("aria-pressed", String(i === index)));
}

letters.forEach(([ch, name], i) => {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.textContent = ch;
  btn.setAttribute("aria-label", `${ch} — ${name}`);
  btn.addEventListener("click", () => select(i));
  grid.appendChild(btn);
});

select(0);
document.getElementById("host").textContent = window.location.host || "local file";
document.getElementById("loaded").textContent = new Date().toLocaleString("ka-GE");