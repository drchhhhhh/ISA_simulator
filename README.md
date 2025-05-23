# ISA simulator

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif"><br>

## Contents 📘  
- [Introduction](#introduction)  
- [Objective](#objective)  
- [Theory](#theory)  
- [Features](#features)  
- [Purpose](#purpose)  
- [Architecture](#architecture)  
- [Design](#design)  
- [Implementation](#implementation)  
- [Debugging & Test Run](#debugging)  
- [Results & Analysis](#results)  
- [Conclusion & Future Improvements](#conclusion)  
- [Prerequisites](#prereqs)  
- [Member Portfolio](#members)  

---

## <a name="introduction"></a>Introduction 🔧  
**ISA-Sim** is a full-featured 32-bit RISC Instruction Set Architecture simulator, built to support educational and experimental learning in computer architecture. It models pipelined execution, memory systems, and I/O interaction with interactive visualization. The platform acts as a practical companion to theoretical courses.

---

## <a name="objective"></a>Objective 🎯  
The core objective of this project is to **design, build, and analyze** an instruction set simulator that supports:
- ✅ A custom 32-bit RISC ISA with core arithmetic, logical, memory, and control instructions  
- ✅ A fully functional **5-stage pipeline** with hazard detection and forwarding  
- ✅ An assembler for machine code generation  
- ✅ A GUI for **real-time visualization** of register states, memory, and pipeline behavior  
- ✅ Performance metrics (IPC, CPI, stalls, efficiency) to support learning and optimization  

---

## <a name="theory"></a>Theory 🧠  
### Instruction Set Architecture (ISA)
Defines the interface between software and hardware. ISA-Sim implements a **fixed-length, load-store RISC architecture** with:
- 32-bit instructions  
- 32 general-purpose registers  
- Immediate and register addressing  

### Instruction Categories  
- **Arithmetic**: ADD, SUB, MUL, DIV  
- **Logical**: AND, OR, XOR  
- **Memory**: STORE  
- **Control**: HALT  

### Pipeline Model  
- **Stages**: Fetch → Decode → Execute → Memory → Writeback  
- **Ideal CPI** = 1.0 | **Actual CPI** = 1 + (Stalls / Instructions)  
- **Hazard Resolution**: RAW detection, forwarding (EX/MEM, MEM/WB)  

---

## <a name="features"></a>Features 🚀  
- 32-bit RISC Instruction Set  
- 5-Stage Pipeline with hazard detection and forwarding  
- Two-pass Assembler  
- Interactive GUI with visualization of pipeline and registers  
- Performance metrics (IPC, CPI, Efficiency)  
- Memory-mapped I/O with simulated peripherals  
- Complete test suite and robust error handling

---

## <a name="purpose"></a>Purpose 🧭  
**ISA-Sim** serves to:
- Visualize pipelined instruction execution
- Demonstrate hazard detection and mitigation
- Evaluate instruction timing and performance
- Bridge theory and practical system design

---

## <a name="architecture"></a>Architecture 🏗️  
### Frontend: Tkinter GUI  
### Backend: Python modules  
### Key Modules:
- assembler.py
- simulator.py
- alu.py
- memory.py
- register_file.py
- control_unit.py
- pipeline_register.py
- visualizer.py

---

## <a name="design"></a>Design Blueprint 🧩  
- Register File with 32 GPRs, PC, flags  
- ALU for core operations  
- Memory segmentation for code/data/stack/heap/I/O  
- Control Unit for instruction decode  
- Forwarding and hazard detection algorithms  

---

## <a name="implementation"></a>Implementation ⚙️  
| Module | Description |
|--------|-------------|
| assembler.py | Assembly translation |
| simulator.py | Pipeline engine |
| alu.py | ALU logic |
| memory.py | Segmented memory |
| register_file.py | Register file ops |
| control_unit.py | Signal generation |
| pipeline_register.py | Stage registers |
| visualizer.py | GUI visualization |

---

## <a name="debugging"></a>Debugging & Test Run 🔍  
- ✅ Unit Testing  
- ✅ Integration Testing  
- ✅ System Testing  
- ✅ GUI Testing  

Example test case:
```
ADDI R1, R0, #5
ADD R2, R1, R1
STORE R2, [R0+0x10000000]
HALT
```

---

## <a name="results"></a>Results & Analysis 📈  
| Metric | Result |
|--------|--------|
| IPC | 0.73 |
| Efficiency | 65.2% |
| Test Pass Rate | ✅ 12/12 |
- Verified 8 working instructions
- Visual accuracy and hazard resolution confirmed

---

## <a name="conclusion"></a>Conclusion & Future Improvements 🧪  
### ✅ Achievements:
- Working 5-stage pipeline
- Full GUI with metrics
- High educational value

### 🔄 Future:
- Branch instructions
- Cache simulation
- Superscalar pipeline
- Web-based GUI
- Curriculum integration

---

## <a name="prereqs"></a>Prerequisites ⚙️  
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python visualizer.py
```
Dependencies: matplotlib, numpy, Python 3.9+

---

## <a name="members"></a>Member Portfolio 💅  
Aguilar, Rose Ann C.

Arenas, Aldrich Amiel A.

Briones, Sean Kyron Z.

De Jose, Mary Kristine A.

Recto, Nerine Rosette M.

Reyes, Paul Alexis J.

---
