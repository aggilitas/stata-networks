# Networks.ado - Proje Notları

## Tarih: 2026-02-07

### Proje Başlangıcı

Proje hedefi: Node'lar arası ilişkileri network edge'lerine çeviren ve ivreghdfe ile analiz için uygun hale getiren Stata .ado dosyası

### Cevaplanması Gereken Sorular

1. **Giriş Verisi Formatı:**
   - Kullanıcının elinde hangi formatta veri var?
   - Node listesi + ilişki matrisi mi?
   - Panel veri formatında mı?
   
2. **Network Tipi:**
   - Directed (yönlü) / Undirected (yönsüz)?
   - Weighted (ağırlıklı) / Unweighted?
   
3. **ivreghdfe Kullanımı:**
   - Edge'ler bağımlı değişken mi olacak?
   - Network yapısı IV veya FE olarak mı kullanılacak?
   - Hangi tür ekonometrik model kurulacak?
   
4. **Network Metrikleri:**
   - Sadece edge list mi yeterli?
   - Centrality, betweenness, clustering gibi metrikler gerekli mi?

### Teknoloji Seçimleri

- **Dil:** Stata .ado (Mata kullanımı değerlendirilecek)
- **Bağımlılıklar:** ivreghdfe, reghdfe (isteğe bağlı)
- **Veri Yapısı:** TBD (kullanıcı girdisine bağlı)

### Sonraki Adımlar

1. Kullanıcıdan yukarıdaki soruların cevaplarını al
2. Temel .ado dosyası iskeletini oluştur
3. Örnek veri seti hazırla
4. Test senaryoları yaz
5. Dokümantasyon tamamla
