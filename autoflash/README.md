# AutoFlash

Pluggable, çok-platformlu ECU flashing framework **iskeleti** — Autotuner /
KESS3 / Flex gibi profesyonel araçların çekirdek mimarisinin açık, eğitim
amaçlı bir Python karşılığı.

Bu repo **framework**'ü verir; her ECU ailesi için platform-spesifik mantık
(seed/key, container, checksum) ayrı bir `ECUDriver` modülünde yaşar. Tam
referans implementasyon için: [bri3d/VW_Flash](https://github.com/bri3d/VW_Flash).

## Mimari

```
                 +------------------+
   CLI / app  -> |     Flasher      |  orkestrasyon: identify -> read/write
                 +--------+---------+
                          |
        +-----------------+------------------+
        |                                    |
+-------v--------+                  +--------v---------+
|  BaseConnection|                  |    ECUDriver     |  <- platforma OZEL
|  (transport)   |                  |  (plugin)        |
+-------+--------+                  +--------+---------+
        |                                    |
  OBD / Bench / Boot              seed/key, memory map,
  (CAN/ISO-TP, BSL...)            container (enc/comp), checksum
```

| Katman          | Dosya                | Sorumluluk |
|-----------------|----------------------|------------|
| Transport       | `connection.py`      | OBD (CAN/ISO-TP) / Bench / Boot soyutlaması |
| UDS akışı       | `flasher.py`         | session, security access, 0x34/0x36/0x37 |
| Driver arayüzü  | `ecu_driver.py`      | platform-spesifik sözleşme |
| Registry        | `registry.py`        | ECU → driver eşlemesi |
| Örnek driver    | `drivers/simos18.py` | iskelet (açık kaynağa referanslı) |
| CLI             | `cli.py`             | identify / read / write |

## Kurulum

```bash
pip install -r requirements.txt          # python-can, can-isotp, udsoncan
# Linux'ta SocketCAN:
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
```

### Windows

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt pytest
py demo_virtual.py
py -m pytest -q
pytest -q
```

Windows'ta `python` komutu Microsoft Store alias'ina duserse `py` launcher
kullanilabilir veya App Execution Aliases ayarindan `python.exe` / `python3.exe`
kapatilabilir.

Donanım: başlangıç için **Linux + SocketCAN + CANable** yeterli. Bench/Boot
için sonra Tricore BSL probe'u.

## Kullanım

### Sanal ECU (donanım yok) — burada başla

```bash
pip install -r requirements.txt pytest
python demo_virtual.py     # uctan uca demo: identify -> read -> write -> checksum gate
pytest -q                  # regression tests
```

### CLI

```bash
python -m autoflash.cli identify --virtual
python -m autoflash.cli read --virtual --out ./dump
python -m autoflash.cli write --virtual --block CAL --file ./dump/CAL.bin
pytest -q
```

Sanal ECU (`autoflash/virtual.py`) gerçek `udsoncan.Client`'a ham UDS byte
seviyesinde cevap verir; yani Flasher'ın **gerçek kodu** test edilir, sadece
transport sahtedir. Donanıma geçince tek değişiklik:
`VirtualCanConnection` → `IsoTpCanConnection`.

### Gerçek ECU (SocketCAN)

```bash
sudo ip link set can0 type can bitrate 500000 && sudo ip link set up can0
python -m autoflash.cli identify --channel can0
python -m autoflash.cli read     --channel can0 --out ./dump
python -m autoflash.cli write    --channel can0 --block CAL --file ./tune/CAL.bin
```

Donanım: başlangıç için **Linux + SocketCAN + CANable** yeterli.

## Current milestone

- Virtual ECU simulator tamamlandi.
- Mock ECU driver tamamlandi.
- CLI `--virtual` modu tamamlandi.
- Regression tests mevcut.
- Gercek ECU destegi henuz yok.
- Simos18 entegrasyonu sonraki read-only milestone olarak planlaniyor.
- Write/recovery gercek donanimda en sona birakilacak.

## Yeni ECU eklemek

`drivers/` altına yeni bir modül koy, `ECUDriver`'dan türet, `@registry.register`
ile kaydet ve şu metotları doldur: `identify`, `memory_map`, `compute_key`,
`decode_container`, `encode_container`, `correct_checksum`. `drivers/mock.py`
çalışan bir referanstır (sanal ECU ile eşleşir).

## Yol haritası

1. [x] Framework iskeleti
2. [x] **Sanal ECU simülatörü + mock driver + testler** (bu sürüm)
3. [x] Read pipeline (upload 0x35/0x36/0x37) — simülasyonda çalışır
4. [ ] Açık platform (Simos18): VW_Flash'tan checksum + container mantığı
5. [ ] Gerçek donanımda read testi (sahip olunan ECU)
6. [ ] Bench modu (doğrudan pinout)
7. [ ] Boot/BSL (Tricore TC179x kurtarma)
8. [ ] Write/recovery (en sona — brick riski)

## Kapsam / sınır

Bu araç **sahip olduğun veya üzerinde çalışmaya yetkili olduğun** ECU'lar için,
tuning · araştırma · ECU onarımı amaçlıdır. İki şey kapsam dışıdır:

- Belirli bir üreticinin güncel korumasını sıfırdan kırmaya yönelik yeni exploit
  geliştirme (platform-spesifik `compute_key`/`decode_container` stub bırakıldı).
- Emisyon defeat (DPF/EGR/AdBlue/SCR silme) — emisyon mevzuatı kapsamında.

## Referanslar

- `bri3d/VW_Flash`, `bri3d/Simos18_SBOOT`, `bri3d/TC1791_CAN_BSL`
- `pylessard/python-udsoncan` (UDS / ISO-14229)
- python-can, can-isotp (ISO 15765-2)
