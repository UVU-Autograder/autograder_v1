```mermaid
flowchart LR
    %% ---------- Actors ----------
    Student("Student <br/> (Unauthenticated)")
    Instructor("Instructor")
    IA("Teaching Assistant (IA)")
    Admin("Administrator")

    %% ---------- System boundary ----------
    subgraph System["UVU Autograder"]
        subgraph Sandbox["Public sandbox (no account)"]
            UC1(["Discover assignments"])
            UC2(["Manage workspace files"])
            UC3(["Run code & view results"])
            UC4(["Get AI feedback"])
            UC5(["Download my files"])
        end

        subgraph Staff["Staff (sign-in required)"]
            UC6(["Configure modules & concepts"])
            UC7(["Manage assignments"])
            UC8(["Validate assignment"])
            UC9(["Grade Canvas batch"])
            UC10(["Review & grade submissions"])
            UC11(["Export grades & feedback"])
            UC12(["Sign in with university account"])
            UC13(["Run preflight check"])
            UC14(["Manage courses & sections"])
            UC15(["Manage staff access"])
            UC16(["Monitor system health"])
        end
    end

    %% ---------- External systems ----------
    Canvas[["Canvas LMS"]]
    Entra[["Microsoft Entra ID"]]
    Judge0[["Judge0 / Kata sandbox"]]
    AI[["Local vLLM / Gemma"]]

    %% ---------- Actor generalization ----------
    Instructor -->|"inherits"| IA
    Admin -->|"inherits"| Instructor

    %% ---------- Actor associations ----------
    Student --- UC1 & UC2 & UC3 & UC4 & UC5
    Instructor --- UC6 & UC7 & UC8 & UC9
    Admin --- UC14 & UC15 & UC16
    IA --- UC12 & UC10 & UC11
    IA -.-|"view only"| UC6
    IA -.-|"view only"| UC7

    %% ---------- Relationships ----------
    UC4 -.->|"«extend»"| UC3
    UC8 -.->|"«include»"| UC13
    UC9 -.->|"«include»"| UC13

    %% ---------- External systems ----------
    UC3 & UC8 & UC9 --- Judge0
    UC4 --- AI
    UC12 --- Entra
    Canvas -.->|"ZIP export"| UC9
    UC11 -.->|"imported manually into"| Canvas

```