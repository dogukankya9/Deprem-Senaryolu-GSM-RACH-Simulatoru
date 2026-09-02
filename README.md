# Deprem Senaryolu GSM RACH Simülatörü
Bu proje, deprem gibi olağanüstü durumlarda GSM şebekelerinde oluşabilecek ani ve yoğun erişim trafiğini simüle etmek ve RACH (Random Access Channel) üzerindeki yükü yönetmeye yönelik bir model geliştirmektedir.

Sistem; aynı anda gelen çok sayıda erişim isteğini şebeke kapasitesi, RACH çakışması, barring, kullanıcı önceliği, backoff ve timeout mekanizmalarını kullanarak değerlendirir. Şebeke yükü arttıkça barring seviyesi dinamik olarak değişir ve düşük öncelikli trafik sınırlandırılarak kritik haberleşme trafiğinin erişim şansının korunması amaçlanır.

Simülasyonda AFAD, ambulans, itfaiye ve kritik kamu trafiği yüksek öncelikli; normal vatandaş trafiği ise daha düşük öncelikli olarak ele alınmaktadır. RACH çakışması yaşayan erişim istekleri backoff sürecine alınarak belirli bir süre sonra tekrar denenir.

Proje ayrıca anlık şebeke yükü, RACH slot kapasitesi, başarılı erişimler, barring nedeniyle engellenen erişimler, RACH çakışmaları ve timeout değerlerini takip eder. Bunun yanında kullanıcı sınıflarına göre AFAD/kritik trafik ve normal kullanıcı başarı oranları ayrı olarak izlenebilmektedir.

Projenin temel amacı
Deprem anında GSM şebekesinin tamamen kilitlenmesini önlemek, RACH üzerindeki yoğunluğu yönetmek ve kritik haberleşme trafiğinin erişilebilirliğini artıracak bir erişim kontrol yaklaşımını simülasyon ortamında göstermek.
