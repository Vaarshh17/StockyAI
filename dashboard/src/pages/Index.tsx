import { createContext, useContext, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Send,
  Sparkles,
  CloudRain,
  AlertTriangle,
  Bell,
  Phone,
  Package,
  Tag,
  ArrowLeftRight,
  Wallet,
  Plus,
  Sprout,
  TrendingDown,
  TrendingUp,
  Languages,
} from "lucide-react";
import plantLogo from "@/assets/plantlogo.png";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const LANG_LABEL: Record<"en" | "ms" | "zh", string> = { en: "EN", ms: "BM", zh: "中文" };
const LANG_FULL: Record<"en" | "ms" | "zh", string> = {
  en: "English",
  ms: "Bahasa Melayu",
  zh: "中文 (Chinese)",
};

/* ---------- i18n ---------- */
type Lang = "en" | "ms" | "zh";
const dict = {
  en: {
    tagline: "",
    openChat: "Open chat",
    greeting: "Good morning, Boss.",
    glance: "Here's your morning at a glance.",
    thisWeek: "This week",
    recentWeeks: "Recent weeks",
    pastMonths: "Past months",
    today: "Today",
    week: "Week",
    month: "Month",
    futureDates: "Future dates",
    upcoming: "upcoming",
    withReminders: "with reminders",
    upcomingLabel: "Upcoming",
    reminder: "reminder",
    reminders: "reminders",
    viewInTg: "View in Telegram",
    open: "Open",
    discuss: "Discuss",
    discussInTg: "Discuss in Telegram",
    morningBrief: "Morning Brief",
    alerts: "alerts",
    remindersTitle: "Reminders",
    pending: "pending",
    addReminder: "Add reminder via Telegram",
    headsUp: "Stocky sent 30-min heads-up ✓",
    done: "Done",
    inventory: "Inventory Status",
    critical: "critical",
    item: "Item",
    stock: "Stock",
    expiry: "Expiry",
    status: "Status",
    supplierPrices: "Supplier Prices",
    cheapest: "Cheapest",
    aboveBenchmark: "Above benchmark",
    tradeLog: "Trade Log",
    buys: "buys",
    sales: "sales",
    logTrade: "Log new trade",
    receivables: "Receivables",
    overdue: "overdue",
    draftFollowUp: "Draft Follow-up",
    sales2: "Sales",
    buys2: "Buys",
    topMovers: "Top movers",
    spoilageAlerts: "spoilage alerts",
    overdueRec: "overdue receivables",
    instinctFired: "Stocky's Instinct fired",
    instinctText: "Cabai variance crossed 12% — supplier shift recommended.",
    fridayDigest: "View Friday digest",
    revenue: "Revenue",
    cost: "Cost",
    bestCommodity: "Best commodity",
    worstSupplier: "Worst supplier",
    creditOut: "Credit outstanding",
    instinctHighlights: "Instinct highlights",
    monthlyDigest: "Open monthly digest",
    instinctTitle: "Stocky's Instinct",
    instinctBody1: "Bayam sell velocity dropped",
    instinctBody2: "the same week Pak Ali raised prices — buyers may be substituting. Consider switching to",
    instinctBody3: "next week.",
    briefBayam: "low (18kg) &",
    briefBayamEnd: "expires today.",
    briefOverdue: "overdue receivables totalling",
    briefRain: "Heavy rain expected — leafy greens demand may dip in afternoon.",
    suggests: "Stocky suggests:",
    suggestsBody: "Push taugeh promo before 11am, hold off bayam restock until tomorrow.",
    viewBrief: "View brief in Telegram",
    due: "Due",
  },
  ms: {
    tagline: "Risikan pasar basah",
    openChat: "Buka sembang",
    greeting: "Selamat pagi, Boss.",
    glance: "Ini ringkasan pagi anda.",
    thisWeek: "Minggu ini",
    recentWeeks: "Minggu lepas",
    pastMonths: "Bulan lepas",
    today: "Hari ini",
    week: "Minggu",
    month: "Bulan",
    futureDates: "Tarikh akan datang",
    upcoming: "akan datang",
    withReminders: "ada peringatan",
    upcomingLabel: "Akan datang",
    reminder: "peringatan",
    reminders: "peringatan",
    viewInTg: "Lihat di Telegram",
    open: "Buka",
    discuss: "Bincang",
    discussInTg: "Bincang di Telegram",
    morningBrief: "Taklimat Pagi",
    alerts: "amaran",
    remindersTitle: "Peringatan",
    pending: "tertangguh",
    addReminder: "Tambah peringatan via Telegram",
    headsUp: "Stocky hantar peringatan 30-minit ✓",
    done: "Selesai",
    inventory: "Status Stok",
    critical: "kritikal",
    item: "Barang",
    stock: "Stok",
    expiry: "Tamat",
    status: "Status",
    supplierPrices: "Harga Pembekal",
    cheapest: "Termurah",
    aboveBenchmark: "Atas penanda aras",
    tradeLog: "Log Dagangan",
    buys: "beli",
    sales: "jual",
    logTrade: "Log dagangan baru",
    receivables: "Penghutang",
    overdue: "tertunggak",
    draftFollowUp: "Draf Susulan",
    sales2: "Jualan",
    buys2: "Belian",
    topMovers: "Paling laku",
    spoilageAlerts: "amaran rosak",
    overdueRec: "penghutang tertunggak",
    instinctFired: "Naluri Stocky aktif",
    instinctText: "Variasi cabai melepasi 12% — disyorkan tukar pembekal.",
    fridayDigest: "Lihat ringkasan Jumaat",
    revenue: "Hasil",
    cost: "Kos",
    bestCommodity: "Komoditi terbaik",
    worstSupplier: "Pembekal terburuk",
    creditOut: "Kredit tertunggak",
    instinctHighlights: "Sorotan naluri",
    monthlyDigest: "Buka ringkasan bulanan",
    instinctTitle: "Naluri Stocky",
    instinctBody1: "Kelajuan jualan bayam jatuh",
    instinctBody2: "minggu yang sama Pak Ali naikkan harga — pembeli mungkin tukar. Pertimbang tukar ke",
    instinctBody3: "minggu depan.",
    briefBayam: "rendah (18kg) &",
    briefBayamEnd: "tamat hari ini.",
    briefOverdue: "penghutang tertunggak berjumlah",
    briefRain: "Hujan lebat dijangka — permintaan sayur hijau mungkin turun petang.",
    suggests: "Stocky cadang:",
    suggestsBody: "Tolak promosi taugeh sebelum 11pg, tangguh restok bayam hingga esok.",
    viewBrief: "Lihat taklimat di Telegram",
    due: "Tarikh",
  },
  zh: {
    tagline: "湿巴刹智能",
    openChat: "打开对话",
    greeting: "老板，早安。",
    glance: "这是您今早的概览。",
    thisWeek: "本周",
    recentWeeks: "最近几周",
    pastMonths: "过去几个月",
    today: "今天",
    week: "周",
    month: "月",
    futureDates: "未来日期",
    upcoming: "即将到来",
    withReminders: "有提醒",
    upcomingLabel: "即将到来",
    reminder: "项提醒",
    reminders: "项提醒",
    viewInTg: "在 Telegram 查看",
    open: "打开",
    discuss: "讨论",
    discussInTg: "在 Telegram 讨论",
    morningBrief: "晨间简报",
    alerts: "条警报",
    remindersTitle: "提醒",
    pending: "待办",
    addReminder: "通过 Telegram 添加提醒",
    headsUp: "Stocky 已提前 30 分钟提醒 ✓",
    done: "完成",
    inventory: "库存状态",
    critical: "紧急",
    item: "商品",
    stock: "库存",
    expiry: "到期",
    status: "状态",
    supplierPrices: "供应商价格",
    cheapest: "最便宜",
    aboveBenchmark: "高于基准",
    tradeLog: "交易记录",
    buys: "采购",
    sales: "销售",
    logTrade: "记录新交易",
    receivables: "应收账款",
    overdue: "逾期",
    draftFollowUp: "起草跟进",
    sales2: "销售",
    buys2: "采购",
    topMovers: "热销商品",
    spoilageAlerts: "条变质警报",
    overdueRec: "笔逾期应收",
    instinctFired: "Stocky 直觉已触发",
    instinctText: "辣椒价差超过 12% — 建议更换供应商。",
    fridayDigest: "查看周五摘要",
    revenue: "收入",
    cost: "成本",
    bestCommodity: "最佳商品",
    worstSupplier: "最差供应商",
    creditOut: "未结信贷",
    instinctHighlights: "直觉亮点",
    monthlyDigest: "打开月度摘要",
    instinctTitle: "Stocky 的直觉",
    instinctBody1: "菠菜销售速度下降",
    instinctBody2: "与 Pak Ali 涨价同周 — 买家可能在替换。考虑下周改为",
    instinctBody3: "。",
    briefBayam: "库存低 (18kg) &",
    briefBayamEnd: "今天到期。",
    briefOverdue: "笔逾期应收，总额",
    briefRain: "预计有大雨 — 下午绿叶菜需求可能下降。",
    suggests: "Stocky 建议：",
    suggestsBody: "11 点前推销豆芽，菠菜补货推迟到明天。",
    viewBrief: "在 Telegram 查看简报",
    due: "到期",
  },
};

type Translations = typeof dict.en;
const LangContext = createContext<{ lang: Lang; t: Translations }>({
  lang: "en",
  t: dict.en as Translations,
});
const useT = () => useContext(LangContext).t;

const TG_URL = "https://t.me/StockyAIBot";

/* ---------- Telegram pill ---------- */
const TgLink = ({
  label,
  className,
}: {
  label?: string;
  className?: string;
}) => {
  const t = useT();
  return (
    <a
      href={TG_URL}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full bg-telegram px-2.5 py-1 text-[11px] font-medium text-telegram-foreground transition-transform active:scale-95",
        className
      )}
    >
      <Send className="h-3 w-3" strokeWidth={2.4} />
      {label ?? t.viewInTg}
    </a>
  );
};

/* ---------- Mock data ---------- */
const today = new Date();
const localeOf = (lang: Lang) => (lang === "ms" ? "ms-MY" : "en-MY");
const fmtDay = (d: Date, lang: Lang = "en") =>
  d.toLocaleDateString(localeOf(lang), { weekday: "short", day: "numeric", month: "short" });
const fmtFull = (d: Date, lang: Lang = "en") =>
  d.toLocaleDateString(localeOf(lang), { weekday: "long", day: "numeric", month: "long" });

const startOfWeek = (d: Date) => {
  const x = new Date(d);
  const day = (x.getDay() + 6) % 7; // Mon = 0
  x.setDate(x.getDate() - day);
  x.setHours(0, 0, 0, 0);
  return x;
};

const addDays = (d: Date, n: number) => {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
};

const weekStart = startOfWeek(today);
const currentWeek = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

const reminders = [
  { time: "09:00", label: "Call Pak Ali re: weekend stock", type: "call", heads_up: true, done: true },
  { time: "11:00", label: "Check taugeh expiry", type: "stock", done: true },
  { time: "14:30", label: "Confirm Restoran Maju order", type: "general", done: false },
  { time: "16:00", label: "Pickup from Kumar Bros", type: "stock", done: false },
];

const inventory = [
  { item: "Bayam", stock: "18 kg", expiry: "1 day", status: "Critical" },
  { item: "Kangkung", stock: "42 kg", expiry: "2 days", status: "Warning" },
  { item: "Cabai Merah", stock: "26 kg", expiry: "5 days", status: "OK" },
  { item: "Bawang Putih", stock: "55 kg", expiry: "21 days", status: "OK" },
  { item: "Tomato", stock: "11 kg", expiry: "2 days", status: "Warning" },
  { item: "Taugeh", stock: "8 kg", expiry: "Today", status: "Critical" },
];

const prices = [
  { item: "Bayam", supplier: "Pak Ali Segar", price: 3.20, fama: 2.90, cheapest: false },
  { item: "Bayam", supplier: "Ah Seng Trading", price: 2.80, fama: 2.90, cheapest: true },
  { item: "Cabai Merah", supplier: "Kumar Bros", price: 14.50, fama: 13.20, cheapest: false },
  { item: "Cabai Merah", supplier: "Pak Ali Segar", price: 13.00, fama: 13.20, cheapest: true },
  { item: "Taugeh", supplier: "Ah Seng Trading", price: 4.20, fama: 4.00, cheapest: true },
];

const buys = [
  { time: "05:40", item: "Kangkung", qty: "50 kg", price: "RM 95", party: "Pak Ali Segar" },
  { time: "06:10", item: "Cabai Merah", qty: "20 kg", price: "RM 260", party: "Pak Ali Segar" },
  { time: "06:25", item: "Taugeh", qty: "15 kg", price: "RM 63", party: "Ah Seng Trading" },
];

const sales = [
  { time: "07:15", item: "Kangkung", qty: "12 kg", price: "RM 36", party: "Restoran Maju" },
  { time: "08:02", item: "Bayam", qty: "8 kg", price: "RM 32", party: "Kedai Runcit Wangi" },
  { time: "09:40", item: "Cabai Merah", qty: "5 kg", price: "RM 87", party: "Ah Kow Catering" },
];

const receivables = [
  { buyer: "Restoran Maju", amount: 480, due: "18 Apr", status: "Overdue" },
  { buyer: "Kedai Runcit Wangi", amount: 220, due: "26 Apr", status: "Due soon" },
  { buyer: "Ah Kow Catering", amount: 1150, due: "12 Apr", status: "Overdue" },
];

/* ---------- Atoms ---------- */
const SectionShell = ({
  icon: Icon,
  title,
  open,
  onToggle,
  badge,
  children,
}: {
  icon: any;
  title: string;
  open: boolean;
  onToggle: () => void;
  badge?: string;
  children: React.ReactNode;
}) => (
  <div className="overflow-hidden rounded-2xl bg-white">
    <button
      onClick={onToggle}
      className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
    >
      <div className="flex items-center gap-2.5">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-soft text-primary">
          <Icon className="h-4 w-4" />
        </span>
        <span className="font-display text-base font-semibold text-foreground">{title}</span>
        {badge && (
          <span className="rounded-full bg-warning-soft px-2 py-0.5 text-[10px] font-semibold text-warning-foreground">
            {badge}
          </span>
        )}
      </div>
      <ChevronDown
        className={cn(
          "h-4 w-4 text-muted-foreground transition-transform",
          open && "rotate-180"
        )}
      />
    </button>
    {open && <div className="bg-white px-4 py-3">{children}</div>}
  </div>
);

const StatusPill = ({ status }: { status: string }) => {
  const map: Record<string, string> = {
    OK: "bg-success-soft text-success",
    Warning: "bg-warning-soft text-warning",
    Critical: "bg-destructive-soft text-destructive",
    Overdue: "bg-destructive-soft text-destructive",
    "Due soon": "bg-warning-soft text-warning",
    Paid: "bg-success-soft text-success",
  };
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-[10px] font-semibold",
        map[status] ?? "bg-muted text-muted-foreground"
      )}
    >
      {status}
    </span>
  );
};

/* ---------- Day card ---------- */
const DayCard = ({
  date,
  isToday,
  defaultOpen,
  isFriday,
}: {
  date: Date;
  isToday: boolean;
  defaultOpen: boolean;
  isFriday?: boolean;
}) => {
  const t = useT();
  const { lang } = useContext(LangContext);
  const [open, setOpen] = useState(defaultOpen);
  const [section, setSection] = useState<string | null>(isToday ? "brief" : null);
  const [tradeTab, setTradeTab] = useState<"buys" | "sales">("buys");

  const toggle = (k: string) => setSection(section === k ? null : k);

  return (
    <div className="rounded-2xl bg-card transition-all">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3.5 text-left"
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "flex h-11 w-11 flex-col items-center justify-center gap-px rounded-xl text-center leading-tight",
              isToday ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
            )}
          >
            <span className="text-[10px] font-medium uppercase tracking-wide opacity-80 leading-none">
              {date.toLocaleDateString(localeOf(lang), { weekday: "short" })}
            </span>
            <span className="font-display text-lg font-semibold leading-none">{date.getDate()}</span>
          </div>
          <div>
            <div className="font-display text-base font-semibold leading-tight">
              {isToday ? t.today : fmtDay(date, lang)}
            </div>
            <div className="text-xs text-muted-foreground">{fmtFull(date, lang)}</div>
          </div>
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-muted-foreground transition-transform",
            open && "rotate-180"
          )}
        />
      </button>

      {open && (
        <div className="space-y-2.5 bg-[#f6f6f6] px-3 py-3">
          {/* Friday Instinct */}
          {isFriday && (
            <div className="rounded-2xl bg-gradient-instinct p-3.5">
              <div className="mb-1.5 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-secondary" />
                <span className="font-display text-sm font-semibold text-foreground">
                  {t.instinctTitle}
                </span>
              </div>
              <p className="text-[13px] leading-relaxed text-foreground/90">
                {t.instinctBody1} <strong>40%</strong> {t.instinctBody2}{" "}
                <strong>kangkung</strong> {t.instinctBody3}
              </p>
              <div className="mt-2.5">
                <TgLink label={t.discussInTg} />
              </div>
            </div>
          )}

          {/* 1. Morning Brief */}
          <SectionShell
            icon={CloudRain}
            title={t.morningBrief}
            open={section === "brief"}
            onToggle={() => toggle("brief")}
            badge={`3 ${t.alerts}`}
          >
            <ul className="space-y-2 text-[13px]">
              <li className="flex gap-2">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                <span>
                  <strong>Bayam</strong> {t.briefBayam} <strong>Taugeh</strong> {t.briefBayamEnd}
                </span>
              </li>
              <li className="flex gap-2">
                <Wallet className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                <span>
                  2 {t.briefOverdue} <strong>RM 1,630</strong>.
                </span>
              </li>
              <li className="flex gap-2">
                <CloudRain className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                <span>{t.briefRain}</span>
              </li>
              <li className="flex gap-2 rounded-xl bg-secondary-soft p-2.5">
                <Sprout className="mt-0.5 h-4 w-4 shrink-0 text-secondary" />
                <span>
                  <strong>{t.suggests}</strong> {t.suggestsBody}
                </span>
              </li>
            </ul>
            <div className="mt-3">
              <TgLink label={t.viewBrief} />
            </div>
          </SectionShell>

          {/* 2. Reminders */}
          <SectionShell
            icon={Bell}
            title={t.remindersTitle}
            open={section === "reminders"}
            onToggle={() => toggle("reminders")}
            badge={`${reminders.filter((r) => !r.done).length} ${t.pending}`}
          >
            <ul className="space-y-2">
              {reminders.map((r, i) => (
                <li
                  key={i}
                  className={cn(
                    "flex items-center justify-between gap-2 rounded-xl bg-card px-3 py-2",
                    r.done && "opacity-50"
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    <span className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg bg-muted">
                      {r.type === "call" ? (
                        <Phone className="h-3.5 w-3.5 text-primary" />
                      ) : r.type === "stock" ? (
                        <Package className="h-3.5 w-3.5 text-secondary" />
                      ) : (
                        <Bell className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                    </span>
                    <div>
                      <div className="text-[13px] font-medium leading-tight">
                        <span className="text-muted-foreground">{r.time}</span> · {r.label}
                      </div>
                      {r.heads_up && (
                        <div className="mt-0.5 text-[11px] text-primary">
                          {t.headsUp}
                        </div>
                      )}
                      {r.done && (
                        <div className="mt-0.5 text-[11px] text-muted-foreground">{t.done}</div>
                      )}
                    </div>
                  </div>
                  <TgLink label={t.open} />
                </li>
              ))}
            </ul>
            <a
              href={TG_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl bg-primary-soft py-2 text-[13px] font-medium text-primary transition active:scale-[0.99]"
            >
              <Plus className="h-4 w-4" /> {t.addReminder}
            </a>
          </SectionShell>

          {/* 3. Inventory */}
          <SectionShell
            icon={Package}
            title={t.inventory}
            open={section === "inv"}
            onToggle={() => toggle("inv")}
            badge={`2 ${t.critical}`}
          >
            <div className="overflow-x-auto rounded-xl">
              <table className="w-full min-w-[400px] text-[12px]">
                <thead className="bg-muted/60 text-muted-foreground">
                  <tr>
                    <th className="px-2.5 py-1.5 text-left font-medium">{t.item}</th>
                    <th className="px-2 py-1.5 text-left font-medium">{t.stock}</th>
                    <th className="px-2 py-1.5 text-left font-medium">{t.expiry}</th>
                    <th className="px-2 py-1.5 text-right font-medium">{t.status}</th>
                  </tr>
                </thead>
                <tbody>
                  {inventory.map((it, i) => (
                    <tr
                      key={i}
                      className={cn(
                        "",
                        it.status === "Warning" && "bg-warning-soft/40",
                        it.status === "Critical" && "bg-destructive-soft/40"
                      )}
                    >
                      <td className="px-2.5 py-2 font-medium">{it.item}</td>
                      <td className="px-2 py-2">{it.stock}</td>
                      <td className="px-2 py-2">{it.expiry}</td>
                      <td className="px-2 py-2 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <StatusPill status={it.status} />
                          {it.status !== "OK" && <TgLink label={t.open} />}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionShell>

          {/* 4. Supplier Prices */}
          <SectionShell
            icon={Tag}
            title={t.supplierPrices}
            open={section === "prices"}
            onToggle={() => toggle("prices")}
          >
            <div className="space-y-2">
              {prices.map((p, i) => {
                const variance = p.price - p.fama;
                const above = variance > 0;
                return (
                  <div
                    key={i}
                    className="rounded-xl bg-card p-2.5"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-[13px] font-semibold">{p.item}</div>
                        <div className="text-[11px] text-muted-foreground">{p.supplier}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-display text-sm font-semibold">
                          RM {p.price.toFixed(2)}
                        </div>
                        <div
                          className={cn(
                            "flex items-center justify-end gap-0.5 text-[10px] font-medium",
                            above ? "text-destructive" : "text-success"
                          )}
                        >
                          {above ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          {above ? "+" : ""}
                          {variance.toFixed(2)} vs FAMA
                        </div>
                      </div>
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      <div className="flex gap-1.5">
                        {p.cheapest && (
                          <span className="rounded-full bg-success-soft px-2 py-0.5 text-[10px] font-semibold text-success">
                            {t.cheapest}
                          </span>
                        )}
                        {above && (
                          <span className="rounded-full bg-destructive-soft px-2 py-0.5 text-[10px] font-semibold text-destructive">
                            {t.aboveBenchmark}
                          </span>
                        )}
                      </div>
                      <TgLink label={t.discuss} />
                    </div>
                  </div>
                );
              })}
            </div>
          </SectionShell>

          {/* 5. Trade Log */}
          <SectionShell
            icon={ArrowLeftRight}
            title={t.tradeLog}
            open={section === "trade"}
            onToggle={() => toggle("trade")}
          >
            <div className="mb-2.5 inline-flex rounded-full bg-muted p-0.5">
              {(["buys", "sales"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setTradeTab(tab)}
                  className={cn(
                    "rounded-full px-4 py-1.5 text-[12px] font-medium capitalize transition",
                    tradeTab === tab
                      ? "bg-card text-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {tab === "buys" ? t.buys2 : t.sales2}
                </button>
              ))}
            </div>
            <ul className="space-y-1.5">
              {(tradeTab === "buys" ? buys : sales).map((trade, i) => (
                <li
                  key={i}
                  className="flex items-center justify-between rounded-xl bg-card px-3 py-2 text-[12px]"
                >
                  <div>
                    <div className="font-medium">
                      {trade.item} <span className="text-muted-foreground">· {trade.qty}</span>
                    </div>
                    <div className="text-[11px] text-muted-foreground">
                      {trade.time} · {trade.party}
                    </div>
                  </div>
                  <div className="font-display text-sm font-semibold">{trade.price}</div>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex justify-end">
              <TgLink label={t.logTrade} />
            </div>
          </SectionShell>

          {/* 6. Receivables */}
          <SectionShell
            icon={Wallet}
            title={t.receivables}
            open={section === "rec"}
            onToggle={() => toggle("rec")}
            badge={`2 ${t.overdue}`}
          >
            <ul className="space-y-2">
              {receivables.map((r, i) => {
                const overdue = r.status === "Overdue";
                return (
                  <li
                    key={i}
                    className={cn(
                      "rounded-xl bg-card p-2.5",
                      overdue && "border-destructive/40 bg-destructive-soft/40"
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-[13px] font-semibold">{r.buyer}</div>
                        <div className="text-[11px] text-muted-foreground">{t.due} {r.due}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-display text-sm font-semibold">
                          RM {r.amount.toFixed(2)}
                        </div>
                        <StatusPill status={r.status} />
                      </div>
                    </div>
                    {overdue && (
                      <div className="mt-2 flex items-center justify-between gap-2">
                        <a
                          href={TG_URL}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-full bg-destructive px-3 py-1 text-[11px] font-medium text-destructive-foreground"
                        >
                          {t.draftFollowUp}
                        </a>
                        <TgLink label={t.open} />
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </SectionShell>
        </div>
      )}
    </div>
  );
};

/* ---------- Week summary (past) ---------- */
const WeekSummaryCard = ({
  rangeLabel,
  buys,
  sales,
  topMovers,
  spoilage,
  overdue,
  hasInstinct,
}: {
  rangeLabel: string;
  buys: number;
  sales: number;
  topMovers: string[];
  spoilage: number;
  overdue: number;
  hasInstinct?: boolean;
}) => {
  const t = useT();
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-2xl bg-card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {t.week}
          </div>
          <div className="font-display text-base font-semibold">{rangeLabel}</div>
        </div>
        <ChevronRight
          className={cn("h-4 w-4 text-muted-foreground transition-transform", open && "rotate-90")}
        />
      </button>
      {open && (
        <div className="space-y-3 px-4 py-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-xl bg-success-soft p-2.5">
              <div className="text-[10px] font-medium uppercase text-success">{t.sales2}</div>
              <div className="font-display text-base font-semibold">RM {sales.toLocaleString()}</div>
            </div>
            <div className="rounded-xl bg-secondary-soft p-2.5">
              <div className="text-[10px] font-medium uppercase text-secondary-foreground/70">
                {t.buys2}
              </div>
              <div className="font-display text-base font-semibold">RM {buys.toLocaleString()}</div>
            </div>
          </div>
          <div>
            <div className="text-[11px] font-medium text-muted-foreground">{t.topMovers}</div>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {topMovers.map((m) => (
                <span
                  key={m}
                  className="rounded-full bg-primary-soft px-2.5 py-0.5 text-[11px] font-medium text-primary"
                >
                  {m}
                </span>
              ))}
            </div>
          </div>
          <div className="flex justify-between text-[12px]">
            <span>
              <strong>{spoilage}</strong>{" "}
              <span className="text-muted-foreground">{t.spoilageAlerts}</span>
            </span>
            <span>
              <strong>{overdue}</strong>{" "}
              <span className="text-muted-foreground">{t.overdueRec}</span>
            </span>
          </div>
          {hasInstinct && (
            <div className="rounded-xl bg-gradient-instinct p-2.5 text-[12px]">
              <div className="mb-0.5 flex items-center gap-1.5 font-semibold">
                <Sparkles className="h-3.5 w-3.5 text-secondary" /> {t.instinctFired}
              </div>
              <p className="text-foreground/80">
                {t.instinctText}
              </p>
            </div>
          )}
          <TgLink label={t.fridayDigest} />
        </div>
      )}
    </div>
  );
};

/* ---------- Month summary ---------- */
const MonthSummaryCard = ({
  label,
  revenue,
  cost,
  best,
  worst,
  credit,
  instincts,
}: {
  label: string;
  revenue: number;
  cost: number;
  best: string;
  worst: string;
  credit: number;
  instincts: number;
}) => {
  const t = useT();
  const [open, setOpen] = useState(false);
  const profit = revenue - cost;
  return (
    <div className="rounded-2xl bg-card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {t.month}
          </div>
          <div className="font-display text-base font-semibold">{label}</div>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-success-soft px-2 py-0.5 text-[11px] font-semibold text-success">
            +RM {profit.toLocaleString()}
          </span>
          <ChevronRight
            className={cn(
              "h-4 w-4 text-muted-foreground transition-transform",
              open && "rotate-90"
            )}
          />
        </div>
      </button>
      {open && (
        <div className="space-y-3 border-t border-border/60 px-4 py-3 text-[13px]">
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-xl bg-success-soft p-2.5">
              <div className="text-[10px] font-medium uppercase text-success">{t.revenue}</div>
              <div className="font-display text-base font-semibold">
                RM {revenue.toLocaleString()}
              </div>
            </div>
            <div className="rounded-xl bg-muted p-2.5">
              <div className="text-[10px] font-medium uppercase text-muted-foreground">{t.cost}</div>
              <div className="font-display text-base font-semibold">
                RM {cost.toLocaleString()}
              </div>
            </div>
          </div>
          <div className="space-y-1.5">
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.bestCommodity}</span>
              <strong>{best}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.worstSupplier}</span>
              <strong>{worst}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.creditOut}</span>
              <strong>RM {credit.toLocaleString()}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t.instinctHighlights}</span>
              <strong>{instincts}</strong>
            </div>
          </div>
          <TgLink label={t.monthlyDigest} />
        </div>
      )}
    </div>
  );
};

/* ---------- Future dates group ---------- */
// Mock: which upcoming weekdays already have reminders scheduled
const upcomingReminders: Record<string, { time: string; label: string; type: string }[]> = {
  // by weekday number (0=Sun..6=Sat)
  2: [{ time: "10:00", label: "Meeting with Kumar Bros", type: "general" }],
  4: [
    { time: "08:30", label: "Call Ah Seng re: cabai supply", type: "call" },
    { time: "15:00", label: "Stock check — bawang putih", type: "stock" },
  ],
  6: [{ time: "06:00", label: "Weekend rush prep", type: "stock" }],
};

const FutureDatesGroup = ({ dates }: { dates: Date[] }) => {
  const t = useT();
  const { lang } = useContext(LangContext);
  const [open, setOpen] = useState(false);
  if (dates.length === 0) return null;
  const withReminders = dates.filter((d) => upcomingReminders[d.getDay()]?.length).length;

  return (
    <div className="mb-3 rounded-2xl bg-card">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <div>
          <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            {t.futureDates}
          </div>
          <div className="font-display text-base font-semibold">
            {dates.length} {t.upcoming}{" "}
            {withReminders > 0 && (
              <span className="ml-1 rounded-full bg-primary-soft px-2 py-0.5 text-[10px] font-semibold text-primary">
                {withReminders} {t.withReminders}
              </span>
            )}
          </div>
        </div>
        <ChevronRight
          className={cn("h-4 w-4 text-muted-foreground transition-transform", open && "rotate-90")}
        />
      </button>
      {open && (
        <div className="space-y-2 border-t border-border/60 px-3 py-3">
          {dates.map((d, i) => {
            const rems = upcomingReminders[d.getDay()] ?? [];
            const hasRems = rems.length > 0;
            return (
              <div
                key={i}
                className={cn(
                  "flex items-start gap-3 rounded-xl border px-3 py-2.5",
                  hasRems
                    ? "border-primary/30 bg-primary-soft/40"
                    : "border-dashed border-border bg-card/40"
                )}
              >
                <div
                  className={cn(
                    "flex h-10 w-10 flex-col items-center justify-center rounded-xl",
                    hasRems
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted/60 text-muted-foreground"
                  )}
                >
                  <span className="text-[10px] uppercase opacity-80">
                    {d.toLocaleDateString(localeOf(lang), { weekday: "short" })}
                  </span>
                  <span className="font-display text-base font-semibold">{d.getDate()}</span>
                </div>
                <div className="flex-1">
                  <div
                    className={cn(
                      "text-[13px] font-medium",
                      hasRems ? "text-foreground" : "text-muted-foreground"
                    )}
                  >
                    {hasRems
                      ? `${rems.length} ${rems.length > 1 ? t.reminders : t.reminder}`
                      : t.upcomingLabel}
                  </div>
                  {hasRems && (
                    <ul className="mt-1 space-y-0.5">
                      {rems.map((r, j) => (
                        <li key={j} className="text-[11px] text-foreground/80">
                          <span className="text-muted-foreground">{r.time}</span> · {r.label}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                {hasRems && <TgLink label={t.open} />}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
const Index = () => {
  const [lang, setLang] = useState<Lang>("en");
  const [recentWeeksOpen, setRecentWeeksOpen] = useState(true);
  const [pastMonthsOpen, setPastMonthsOpen] = useState(true);
  const t = dict[lang];
  const monthLabel = today.toLocaleDateString(localeOf(lang), { month: "long", year: "numeric" });

  // Past weeks (mock 2)
  const lastWeekStart = addDays(weekStart, -7);
  const twoWeeksAgo = addDays(weekStart, -14);
  const rangeLabel = (s: Date) =>
    `${s.getDate()} ${s.toLocaleDateString(localeOf(lang), { month: "short" })} – ${addDays(s, 6).getDate()} ${addDays(s, 6).toLocaleDateString(localeOf(lang), { month: "short" })}`;

  return (
    <LangContext.Provider value={{ lang, t }}>
      <div className="min-h-screen bg-background">
        <div className="mx-auto w-full max-w-[390px] px-4 pb-16 pt-5">
          {/* Header */}
          <header className="mb-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <img src={plantLogo} alt="Plant logo" className="h-10 w-10" />
                <div>
                  <h1 className="font-display text-xl font-semibold leading-none">Stocky AI</h1>
                  <p className="text-[11px] text-muted-foreground">{t.tagline}</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      aria-label="Switch language"
                      className="inline-flex items-center gap-1 rounded-full border border-border bg-card px-2.5 py-1 text-[11px] font-semibold text-foreground transition active:scale-95"
                    >
                      <Languages className="h-3.5 w-3.5 text-primary" />
                      {LANG_LABEL[lang]}
                      <ChevronDown className="h-3 w-3 text-muted-foreground" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="min-w-[9rem]">
                    {(["en", "ms", "zh"] as const).map((l) => (
                      <DropdownMenuItem
                        key={l}
                        onClick={() => setLang(l)}
                        className={cn(lang === l && "bg-primary-soft text-primary font-semibold")}
                      >
                        {LANG_FULL[l]}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
                <TgLink label={t.openChat} />
              </div>
            </div>
            <p className="mt-4 text-[13px] text-muted-foreground">
              <span className="font-medium text-foreground">{t.greeting}</span> {t.glance}
            </p>
          </header>

          {/* Current month label */}
          <div className="mb-2 flex items-center justify-between px-1">
            <h2 className="font-display text-lg font-semibold">{monthLabel}</h2>
            <span className="text-[11px] font-medium text-muted-foreground">{t.thisWeek}</span>
          </div>

          {/* Future dates (collapsed group) — shown above today */}
          <FutureDatesGroup
            dates={currentWeek.filter(
              (d) => d > today && d.toDateString() !== today.toDateString()
            )}
          />

          {/* Current week — today + past days (most recent first) */}
          <div className="space-y-2.5">
            {currentWeek
              .filter((d) => d.toDateString() === today.toDateString() || d < today)
              .sort((a, b) => b.getTime() - a.getTime())
              .map((d, i) => {
                const isToday = d.toDateString() === today.toDateString();
                const isPast = !isToday;
                const isFriday = d.getDay() === 5;
                return (
                  <DayCard
                    key={i}
                    date={d}
                    isToday={isToday}
                    defaultOpen={isToday}
                    isFriday={isFriday && isPast}
                  />
                );
              })}
          </div>

          {/* Past weeks */}
          <div className="mt-6 mb-2 flex items-center justify-between px-1">
            <button
              onClick={() => setRecentWeeksOpen(!recentWeeksOpen)}
              className="flex items-center gap-2 text-left"
            >
              <h2 className="font-display text-lg font-semibold">{t.recentWeeks}</h2>
              <ChevronRight
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform",
                  recentWeeksOpen && "rotate-90"
                )}
              />
            </button>
          </div>
          {recentWeeksOpen && (
            <div className="space-y-2.5">
              <WeekSummaryCard
                rangeLabel={rangeLabel(lastWeekStart)}
                buys={4820}
                sales={6240}
                topMovers={["Kangkung", "Cabai Merah", "Bayam"]}
                spoilage={3}
                overdue={2}
                hasInstinct
              />
              <WeekSummaryCard
                rangeLabel={rangeLabel(twoWeeksAgo)}
                buys={5110}
                sales={6020}
                topMovers={["Bayam", "Tomato", "Taugeh"]}
                spoilage={1}
                overdue={1}
              />
            </div>
          )}

          {/* Past months */}
          <div className="mt-6 mb-2 flex items-center justify-between px-1">
            <button
              onClick={() => setPastMonthsOpen(!pastMonthsOpen)}
              className="flex items-center gap-2 text-left"
            >
              <h2 className="font-display text-lg font-semibold">{t.pastMonths}</h2>
              <ChevronRight
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform",
                  pastMonthsOpen && "rotate-90"
                )}
              />
            </button>
          </div>
          {pastMonthsOpen && (
            <div className="space-y-2.5">
              <MonthSummaryCard
                label="March 2026"
                revenue={28450}
                cost={21200}
                best="Cabai Merah"
                worst="Kumar Bros"
                credit={3120}
                instincts={4}
              />
              <MonthSummaryCard
                label="February 2026"
                revenue={25980}
                cost={20100}
                best="Kangkung"
                worst="Pak Ali Segar"
                credit={2480}
                instincts={2}
              />
            </div>
          )}

          <footer className="mt-10 text-center text-[11px] text-muted-foreground">
            {lang === "en"
              ? "Stocky chats with you on Telegram. This dashboard is your quiet view."
              : lang === "ms"
              ? "Stocky berbual dengan anda di Telegram. Dashboard ini pandangan tenang anda."
              : "Stocky 在 Telegram 与您对话。此仪表板是您安静的视图。"}
          </footer>
        </div>
      </div>
    </LangContext.Provider>
  );
};

export default Index;
