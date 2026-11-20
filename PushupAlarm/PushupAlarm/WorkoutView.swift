import SwiftUI

struct WorkoutView: View {
    @StateObject private var session = WorkoutSession()
    let onClose: () -> Void

    var body: some View {
        ZStack {
            (session.finished ? Color.green : Color.black).ignoresSafeArea()

            VStack(spacing: 28) {
                if session.finished {
                    Text("💪").font(.system(size: 100))
                    Text("Красава! Доброе утро")
                        .font(.largeTitle.bold()).foregroundStyle(.white)
                    Button("Я проснулся") { onClose() }
                        .buttonStyle(.borderedProminent).tint(.white).foregroundStyle(.green)
                        .controlSize(.large)
                } else {
                    Text("Отжимайся").font(.title2).foregroundStyle(.white.opacity(0.6))
                    Text("\(session.count) / \(session.target)")
                        .font(.system(size: 96, weight: .black, design: .rounded))
                        .monospacedDigit()
                        .foregroundStyle(.white)
                    ProgressView(value: Double(session.count), total: Double(session.target))
                        .tint(.orange)
                        .scaleEffect(y: 3)
                    Text(session.sensorAvailable
                         ? "Телефон на пол экраном вверх, верх под лицо. Опускайся до самого экрана."
                         : "На этом устройстве нет датчика приближения 😕")
                        .multilineTextAlignment(.center)
                        .foregroundStyle(.white.opacity(0.7))
                }
            }
            .padding(32)
        }
        .onAppear { session.begin() }
        .onDisappear { session.close() }
    }
}
