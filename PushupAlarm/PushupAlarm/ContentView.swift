import SwiftUI

struct ContentView: View {
    @AppStorage("enabled") private var enabled = false
    @AppStorage("hour") private var hour = 7
    @AppStorage("minute") private var minute = 0
    @AppStorage("target") private var target = 20

    @State private var authorized = true
    @State private var status: String?

    private var time: Binding<Date> {
        Binding(
            get: { Calendar.current.date(from: DateComponents(hour: hour, minute: minute)) ?? .now },
            set: {
                let c = Calendar.current.dateComponents([.hour, .minute], from: $0)
                hour = c.hour ?? 7
                minute = c.minute ?? 0
            }
        )
    }

    var body: some View {
        NavigationStack {
            Form {
                if !authorized {
                    Section {
                        Text("Нет доступа к будильникам. Включи в Настройках → Отжимайся → Будильники.")
                            .foregroundStyle(.red)
                    }
                }

                Section {
                    Toggle("Будильник включён", isOn: $enabled)
                    DatePicker("Время", selection: time, displayedComponents: .hourAndMinute)
                    Stepper("Отжиманий: \(target)", value: $target, in: 5...200, step: 5)
                } footer: {
                    Text("Звонит каждый день. Кнопка «Стоп» не поможет: через минуту зазвонит снова, пока не сделаешь норму.")
                }

                Section {
                    Button("Проверить: зазвонит через 1 минуту") {
                        Task {
                            do {
                                try await AlarmService.scheduleTest(in: 60)
                                status = "Тестовый будильник через минуту. Можно заблокировать телефон."
                            } catch {
                                status = "Ошибка: \(error.localizedDescription)"
                            }
                        }
                    }
                    if let status { Text(status).font(.footnote).foregroundStyle(.secondary) }
                }

                Section("Как отжиматься") {
                    Label("Положи телефон на пол экраном вверх, верхним краем под лицо.", systemImage: "iphone")
                    Label("Опускайся, пока лицо или грудь не окажутся в паре сантиметров от экрана. Экран погаснет, это нормально.", systemImage: "arrow.down")
                    Label("Поднялся: отжимание засчитано, телефон скажет номер вслух.", systemImage: "arrow.up")
                }
            }
            .navigationTitle("Отжимайся")
            .task { authorized = await AlarmService.requestAuthorization(); await sync() }
            .onChange(of: enabled) { Task { await sync() } }
            .onChange(of: hour) { Task { await sync() } }
            .onChange(of: minute) { Task { await sync() } }
            .onChange(of: target) { Task { await sync() } }
        }
    }

    private func sync() async {
        guard enabled else { AlarmService.cancelMain(); return }
        do {
            try await AlarmService.scheduleMain(hour: hour, minute: minute)
            status = String(format: "Зазвонит в %02d:%02d", hour, minute)
        } catch {
            status = "Не получилось поставить будильник: \(error.localizedDescription)"
        }
    }
}
