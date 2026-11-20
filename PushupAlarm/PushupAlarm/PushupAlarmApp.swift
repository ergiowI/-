import SwiftUI

@main
struct PushupAlarmApp: App {
    var body: some Scene {
        WindowGroup { RootView() }
    }
}

struct RootView: View {
    @AppStorage("sessionActive") private var sessionActive = false
    @State private var showWorkout = false
    @Environment(\.scenePhase) private var phase

    var body: some View {
        ContentView()
            .fullScreenCover(isPresented: $showWorkout) {
                WorkoutView { showWorkout = false }
            }
            .onAppear { if Settings.sessionActive { showWorkout = true } }
            .onChange(of: sessionActive) { _, active in if active { showWorkout = true } }
            .onChange(of: phase) { _, p in
                if p == .active, Settings.sessionActive { showWorkout = true }
            }
    }
}
