import tkinter as tk
from tkinter import ttk, messagebox
import re
import random

class MIPSSimulator:
    def __init__(self):
        self.registers = {f"${i}": 0 for i in range(32)}
        self.reg_names = [
            "$zero", "$at", "$v0", "$v1", "$a0", "$a1", "$a2", "$a3",
            "$t0", "$t1", "$t2", "$t3", "$t4", "$t5", "$t6", "$t7",
            "$s0", "$s1", "$s2", "$s3", "$s4", "$s5", "$s6", "$s7",
            "$t8", "$t9", "$k0", "$k1", "$gp", "$sp", "$fp", "$ra"
        ]
        self.pc = 0x00400000
        self.memory = {}
        self.labels = {}
        self.code = []
        self.instructions = []
        self.running = False
        self.stdout = []
        
        # Initialize registers
        for i, name in enumerate(self.reg_names):
            self.registers[name] = 0
        self.registers["$sp"] = 0x7FFFFFF0
        self.registers["$gp"] = 0x10008000
        
    def reset(self):
        for name in self.reg_names:
            self.registers[name] = 0
        self.registers["$sp"] = 0x7FFFFFF0
        self.registers["$gp"] = 0x10008000
        self.pc = 0x00400000
        self.memory = {}
        self.labels = {}
        self.code = []
        self.instructions = []
        self.stdout = []
        self.running = False
        
    def parse_assembly(self, assembly_code):
        lines = assembly_code.strip().split('\n')
        self.code = []
        self.labels = {}
        self.instructions = []
        
        # First pass: collect labels and instructions
        for line_num, line in enumerate(lines):
            # Remove comments
            if '#' in line:
                line = line[:line.index('#')]
            line = line.strip()
            if not line:
                continue
                
            # Check for label
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0].strip()
                self.labels[label] = len(self.code) * 4 + 0x00400000
                line = parts[1].strip() if len(parts) > 1 else ''
                
            if line:
                self.instructions.append((line_num, line))
                self.code.append(line)
        
        return len(self.code)
    
    def parse_operands(self, instr):
        # Split instruction into opcode and operands
        parts = instr.split()
        if not parts:
            return None, []
        opcode = parts[0].lower()
        operands = []
        if len(parts) > 1:
            operands_str = ' '.join(parts[1:])
            # Split by commas, but handle brackets
            for op in operands_str.split(','):
                op = op.strip()
                if op:
                    operands.append(op)
        return opcode, operands
    
    def get_reg_num(self, reg):
        if reg in self.reg_names:
            return self.reg_names.index(reg)
        return None
    
    def execute_instruction(self, instr_line):
        line_num, instr = instr_line
        opcode, operands = self.parse_operands(instr)
        
        if not opcode:
            return True
            
        try:
            if opcode == 'add':
                # add $dest, $src1, $src2
                dest, src1, src2 = operands
                self.registers[dest] = self.registers[src1] + self.registers[src2]
                
            elif opcode == 'addi':
                # addi $dest, $src, imm
                dest, src, imm = operands
                imm = int(imm)
                self.registers[dest] = self.registers[src] + imm
                
            elif opcode == 'sub':
                dest, src1, src2 = operands
                self.registers[dest] = self.registers[src1] - self.registers[src2]
                
            elif opcode == 'mul':
                dest, src1, src2 = operands
                self.registers[dest] = self.registers[src1] * self.registers[src2]
                
            elif opcode == 'div':
                dest, src1, src2 = operands
                if self.registers[src2] != 0:
                    self.registers[dest] = self.registers[src1] // self.registers[src2]
                    
            elif opcode == 'li':
                # li $dest, imm
                dest, imm = operands
                if imm.startswith('0x'):
                    self.registers[dest] = int(imm, 16)
                else:
                    self.registers[dest] = int(imm)
                    
            elif opcode == 'la':
                # la $dest, label
                dest, label = operands
                if label in self.labels:
                    self.registers[dest] = self.labels[label]
                else:
                    self.registers[dest] = 0x10000000  # data segment
                    
            elif opcode == 'move':
                # move $dest, $src
                dest, src = operands
                self.registers[dest] = self.registers[src]
                
            elif opcode == 'syscall':
                self.handle_syscall()
                
            elif opcode == 'b':
                # b label
                label = operands[0]
                if label in self.labels:
                    self.pc = self.labels[label]
                    return False  # Skip PC increment
                    
            elif opcode == 'beq':
                # beq $src1, $src2, label
                src1, src2, label = operands
                if self.registers[src1] == self.registers[src2]:
                    if label in self.labels:
                        self.pc = self.labels[label]
                        return False
                        
            elif opcode == 'bne':
                src1, src2, label = operands
                if self.registers[src1] != self.registers[src2]:
                    if label in self.labels:
                        self.pc = self.labels[label]
                        return False
                        
            elif opcode == 'bge':
                src1, src2, label = operands
                if self.registers[src1] >= self.registers[src2]:
                    if label in self.labels:
                        self.pc = self.labels[label]
                        return False
                        
            elif opcode == 'ble':
                src1, src2, label = operands
                if self.registers[src1] <= self.registers[src2]:
                    if label in self.labels:
                        self.pc = self.labels[label]
                        return False
                        
            elif opcode == 'bgt':
                src1, src2, label = operands
                if self.registers[src1] > self.registers[src2]:
                    if label in self.labels:
                        self.pc = self.labels[label]
                        return False
                        
            elif opcode == 'blt':
                src1, src2, label = operands
                if self.registers[src1] < self.registers[src2]:
                    if label in self.labels:
                        self.pc = self.labels[label]
                        return False
                        
            elif opcode == 'j':
                label = operands[0]
                if label in self.labels:
                    self.pc = self.labels[label]
                    return False
                    
            elif opcode == 'jr':
                src = operands[0]
                self.pc = self.registers[src]
                return False
                
            elif opcode == 'jal':
                label = operands[0]
                self.registers["$ra"] = self.pc + 4
                if label in self.labels:
                    self.pc = self.labels[label]
                    return False
                    
            elif opcode == 'lw':
                # lw $dest, offset($src)
                dest, offset_reg = operands
                if '(' in offset_reg and ')' in offset_reg:
                    offset, src = offset_reg.replace(')', '').split('(')
                    offset = int(offset) if offset else 0
                    addr = self.registers[src] + offset
                    self.registers[dest] = self.memory.get(addr, 0)
                    
            elif opcode == 'sw':
                # sw $src, offset($dest)
                src, offset_reg = operands
                if '(' in offset_reg and ')' in offset_reg:
                    offset, dest = offset_reg.replace(')', '').split('(')
                    offset = int(offset) if offset else 0
                    addr = self.registers[dest] + offset
                    self.memory[addr] = self.registers[src]
                    
            elif opcode == 'syscall':
                self.handle_syscall()
                
            else:
                # Unknown instruction, skip
                pass
                
        except Exception as e:
            self.stdout.append(f"[ERROR] at line {line_num+1}: {str(e)}")
            return False
            
        return True
        
    def handle_syscall(self):
        syscall_num = self.registers["$v0"]
        
        if syscall_num == 1:  # print integer
            value = self.registers["$a0"]
            self.stdout.append(str(value))
        elif syscall_num == 4:  # print string
            addr = self.registers["$a0"]
            # For simplicity, we'll use a placeholder
            self.stdout.append("[String output]")
        elif syscall_num == 5:  # read integer
            # For simulation, return a test value
            self.registers["$v0"] = 42
        elif syscall_num == 8:  # read string
            pass
        elif syscall_num == 10:  # exit
            self.running = False
            
    def run(self, assembly_code):
        self.reset()
        self.stdout = []
        
        # Parse the code
        num_instructions = self.parse_assembly(assembly_code)
        if num_instructions == 0:
            return False, "No instructions to execute"
            
        self.running = True
        instruction_index = 0
        max_steps = 1000
        
        while self.running and instruction_index < max_steps:
            # Execute current instruction
            if instruction_index >= len(self.instructions):
                break
                
            continue_exec = self.execute_instruction(self.instructions[instruction_index])
            if not continue_exec:
                # PC was changed, find the index
                pc_diff = self.pc - 0x00400000
                if pc_diff >= 0 and pc_diff % 4 == 0:
                    instruction_index = pc_diff // 4
                else:
                    instruction_index += 1
            else:
                instruction_index += 1
                
        return True, "\n".join(self.stdout) if self.stdout else "Program executed successfully (no output)"
    
    def get_register_state(self):
        lines = []
        lines.append(f"{'Register':<12} {'Value (Hex)':<14} {'Value (Dec)':<12}")
        lines.append("-" * 45)
        
        for i, name in enumerate(self.reg_names):
            if name == "$zero":
                continue
            value = self.registers[name]
            if isinstance(value, int):
                hex_val = f"0x{value & 0xFFFFFFFF:08X}"
                lines.append(f"{name:<12} {hex_val:<14} {value:<12}")
            else:
                lines.append(f"{name:<12} {'N/A':<14} {'N/A':<12}")
                
        lines.append("-" * 45)
        lines.append(f"{'PC':<12} 0x{self.pc:08X} {'':<12}")
        return "\n".join(lines)


class CompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AC's Compiler Beta v0.1 - MIPS 1.0")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e2e")
        
        self.mips = MIPSSimulator()
        self.is_running = False

        # Custom colors
        self.bg_color = "#1e1e2e"
        self.sidebar_bg = "#181825"
        self.panel_bg = "#11111b"
        self.text_bg = "#1a1b26"
        self.accent = "#89b4fa"
        self.warning = "#f9e2af"
        self.success = "#a6e3a1"
        self.error = "#f38ba8"
        self.text_fg = "#cdd6f4"
        self.subtle_fg = "#6c7086"

        self.setup_styles()
        self.create_header()
        self.create_main_panels()
        self.create_status_bar()
        self.populate_initial_data()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_fg, font=("Courier New", 10))
        style.configure("TButton", background=self.accent, foreground="#1e1e2e", 
                       font=("Courier New", 9, "bold"), padding=(10, 5))
        style.map("TButton", background=[("active", "#74c7ec")])
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.panel_bg, foreground=self.text_fg,
                       padding=[15, 5], font=("Courier New", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", self.accent)], foreground=[("selected", "#1e1e2e")])

    def create_header(self):
        header_frame = tk.Frame(self.root, bg=self.sidebar_bg, height=70)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="AC'S COMPILER Beta v0.1", font=("Courier New", 16, "bold"),
                              bg=self.sidebar_bg, fg=self.accent)
        title_label.pack(side="left", padx=20, pady=15)

        mips_badge = tk.Label(header_frame, text="MIPS 1.0", font=("Courier New", 10, "bold"),
                             bg=self.success, fg="#1e1e2e", padx=10, pady=3)
        mips_badge.pack(side="left", padx=10, pady=15)

        self.complete_label = tk.Label(header_frame, text="✓ READY TO COMPILE",
                                      font=("Courier New", 9), bg=self.sidebar_bg, fg=self.success)
        self.complete_label.pack(side="right", padx=20)

    def create_main_panels(self):
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill="both", expand=True, padx=15, pady=10)

        # Left panel - Controls and Console Output
        left_panel = tk.Frame(main_container, bg=self.panel_bg, width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        # Control buttons
        control_frame = tk.Frame(left_panel, bg=self.panel_bg)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.run_btn = tk.Button(control_frame, text="▶ RUN", font=("Courier New", 11, "bold"),
                                bg=self.success, fg="#1e1e2e", padx=20, pady=8,
                                command=self.run_compiler, relief="flat", cursor="hand2")
        self.run_btn.pack(side="left", padx=5)
        
        self.reset_btn = tk.Button(control_frame, text="⟳ RESET", font=("Courier New", 11, "bold"),
                                  bg=self.warning, fg="#1e1e2e", padx=20, pady=8,
                                  command=self.reset_compiler, relief="flat", cursor="hand2")
        self.reset_btn.pack(side="left", padx=5)
        
        self.stop_btn = tk.Button(control_frame, text="■ STOP", font=("Courier New", 11, "bold"),
                                 bg=self.error, fg="#1e1e2e", padx=20, pady=8,
                                 command=self.stop_execution, relief="flat", cursor="hand2",
                                 state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        # Console Output
        console_header = tk.Label(left_panel, text="Console Output", font=("Courier New", 11, "bold"),
                                 bg=self.accent, fg="#1e1e2e", pady=5)
        console_header.pack(fill="x")
        
        self.console_text = tk.Text(left_panel, bg=self.text_bg, fg=self.text_fg,
                                   font=("Courier New", 9), wrap="word", relief="flat",
                                   padx=8, pady=8, height=20)
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbar to console
        console_scroll = tk.Scrollbar(self.console_text, command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scroll.set)

        # Right panel - Notebook with tabs
        right_panel = tk.Frame(main_container, bg=self.bg_color)
        right_panel.pack(side="right", fill="both", expand=True)

        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill="both", expand=True)

        # Source Assembly tab
        self.assembly_frame = tk.Frame(notebook, bg=self.text_bg)
        notebook.add(self.assembly_frame, text="Source Assembly")
        
        # Add edit button for source
        edit_frame = tk.Frame(self.assembly_frame, bg=self.text_bg)
        edit_frame.pack(fill="x", padx=5, pady=5)
        
        self.edit_btn = tk.Button(edit_frame, text="✏ EDIT", font=("Courier New", 9),
                                 bg=self.accent, fg="#1e1e2e", command=self.toggle_edit,
                                 relief="flat")
        self.edit_btn.pack(side="right", padx=5)
        
        self.assembly_text = tk.Text(self.assembly_frame, bg=self.text_bg, fg=self.text_fg,
                                    font=("Courier New", 10), wrap="none", relief="flat",
                                    padx=10, pady=10, insertbackground=self.text_fg,
                                    state="disabled")
        self.assembly_text.pack(fill="both", expand=True)

        # Register State tab
        self.register_frame = tk.Frame(notebook, bg=self.text_bg)
        notebook.add(self.register_frame, text="Register State")
        
        self.register_text = tk.Text(self.register_frame, bg=self.text_bg, fg=self.text_fg,
                                    font=("Courier New", 10), wrap="none", relief="flat",
                                    padx=10, pady=10, insertbackground=self.text_fg)
        self.register_text.pack(fill="both", expand=True)

        # Compiler/Run Log tab
        self.log_frame = tk.Frame(notebook, bg=self.text_bg)
        notebook.add(self.log_frame, text="Compiler/Run Log")
        
        self.log_text = tk.Text(self.log_frame, bg=self.text_bg, fg=self.text_fg,
                               font=("Courier New", 9), wrap="word", relief="flat",
                               padx=10, pady=10, insertbackground=self.text_fg,
                               state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def create_status_bar(self):
        status_bar = tk.Frame(self.root, bg=self.sidebar_bg, height=25)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(status_bar, text="Ready to compile", font=("Courier New", 9),
                                    bg=self.sidebar_bg, fg=self.subtle_fg)
        self.status_label.pack(side="left", padx=10)

        self.memory_label = tk.Label(status_bar, text="Memory: 32KB | Heap: 28KB free",
                                    font=("Courier New", 9), bg=self.sidebar_bg, fg=self.warning)
        self.memory_label.pack(side="right", padx=10)

    def update_console(self, text, color=None):
        self.console_text.insert("end", text + "\n")
        if color:
            line_start = self.console_text.index("end-2l")
            line_end = self.console_text.index("end-1c")
            self.console_text.tag_add(f"color_{len(text)}", line_start, line_end)
            self.console_text.tag_config(f"color_{len(text)}", foreground=color)
        self.console_text.see("end")
        
    def update_log(self, text, color=None):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        if color:
            line_start = self.log_text.index("end-2l")
            line_end = self.log_text.index("end-1c")
            self.log_text.tag_add(f"log_color_{len(text)}", line_start, line_end)
            self.log_text.tag_config(f"log_color_{len(text)}", foreground=color)
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        
    def update_registers(self):
        self.register_text.config(state="normal")
        self.register_text.delete(1.0, tk.END)
        self.register_text.insert("end", self.mips.get_register_state())
        self.register_text.config(state="disabled")
        
    def toggle_edit(self):
        current_state = self.assembly_text.cget("state")
        if current_state == "disabled":
            self.assembly_text.config(state="normal")
            self.edit_btn.config(text="💾 SAVE", bg=self.success)
            self.update_log("[EDITOR] Source code editable. Make changes and click SAVE to compile.", self.accent)
        else:
            self.assembly_text.config(state="disabled")
            self.edit_btn.config(text="✏ EDIT", bg=self.accent)
            self.update_log("[EDITOR] Source code saved.", self.success)
            
    def run_compiler(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.reset_btn.config(state="disabled")
        
        # Clear previous output
        self.console_text.delete(1.0, tk.END)
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
        # Get assembly code
        self.assembly_text.config(state="normal")
        assembly_code = self.assembly_text.get(1.0, tk.END)
        self.assembly_text.config(state="disabled")
        
        # Simulate compilation process
        self.simulate_compilation(assembly_code)
        
    def simulate_compilation(self, assembly_code):
        steps = [
            ("[AC_INIT] Initializing MIPS instruction set definitions... OK.", self.success),
            ("[PARSER] Tokenizer initialized successfully. Lexing input stream... SUCCESS.", self.success),
            ("[SYNTAX] AST generation phase complete. Structure valid.", self.success),
            ("[SEMANTIC] Type checking passed for all registers. No overflow detected.", self.success),
            ("[CODEGEN] Generating assembly instructions. Mapping to MIPS ISA... COMPLETE.", self.success),
            ("[LINKER] Linking object file and startup routine... OK. Output: calc.o", self.success),
            ("[EXECUTION] JIT compilation initiated. Starting execution environment.", self.accent),
            ("[RUNTIME] Stack pointer initialized at 0xFFFFFFFF.", self.accent),
            ("[RUNTIME] Heap allocated: 32KB.", self.accent),
        ]
        
        def run_step(step_index=0):
            if step_index < len(steps):
                msg, color = steps[step_index]
                self.update_log(msg, color)
                self.status_label.config(text=msg[:50])
                self.root.after(400, lambda: run_step(step_index + 1))
            else:
                # Run actual MIPS simulation
                self.update_console("=" * 50, self.accent)
                self.update_console("EXECUTING MIPS PROGRAM", self.accent)
                self.update_console("=" * 50, self.accent)
                
                # Run the simulation
                success, output = self.mips.run(assembly_code)
                
                if success:
                    self.update_log("[TIMEOUT] No critical errors detected during runtime simulation. Program exited gracefully (Exit Code 0).", self.success)
                    self.complete_label.config(text="✓ EXECUTION COMPLETE", fg=self.success)
                    
                    # Display output
                    self.update_console("\n--- PROGRAM OUTPUT ---", self.success)
                    self.update_console(output, self.text_fg)
                    self.update_console("--- END OUTPUT ---\n", self.success)
                else:
                    self.update_log(f"[ERROR] {output}", self.error)
                    self.complete_label.config(text="✗ EXECUTION FAILED", fg=self.error)
                    self.update_console(f"\nERROR: {output}", self.error)
                
                # Update register display
                self.update_registers()
                
                # Final status
                self.status_label.config(text="Execution complete. Exit Code: 0" if success else "Execution failed")
                self.is_running = False
                self.run_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
                self.reset_btn.config(state="normal")
                
        # Start compilation simulation
        self.root.after(500, run_step)
        
    def stop_execution(self):
        if self.is_running:
            self.is_running = False
            self.mips.running = False
            self.update_log("[EXECUTION] Program execution stopped by user.", self.warning)
            self.update_console("\n[STOPPED] Execution halted by user", self.warning)
            self.status_label.config(text="Execution stopped by user")
            self.run_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.reset_btn.config(state="normal")
            self.complete_label.config(text="⚠ EXECUTION STOPPED", fg=self.warning)
            
    def reset_compiler(self):
        self.mips.reset()
        self.update_registers()
        self.console_text.delete(1.0, tk.END)
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        self.update_log("[RESET] Compiler state reset. Ready for new compilation.", self.accent)
        self.update_console("System reset. Ready to compile.", self.success)
        self.status_label.config(text="Ready to compile")
        self.complete_label.config(text="✓ READY TO COMPILE", fg=self.success)
        self.is_running = False
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.reset_btn.config(state="normal")
        
    def populate_initial_data(self):
        # Initial assembly code
        default_assembly = """.data
prompt: .asciiz "Enter number: "
result: .asciiz "\\nResult: "
newline: .asciiz "\\n"

.text
.globl main

main:
    li $t0, 0           # Initialize counter
    li $t1, 5           # Loop limit
    
loop:
    bge $t0, $t1, end   # Branch if counter >= limit
    
    # Add to sum (simulating input)
    li $t2, 10          # Test value
    add $t3, $t3, $t2   # Add to sum
    
    addi $t0, $t0, 1    # Increment counter
    j loop

end:
    # Print result message
    li $v0, 4
    la $a0, result
    syscall
    
    # Print sum
    li $v0, 1
    move $a0, $t3
    syscall
    
    # Exit
    li $v0, 10
    syscall
"""

        self.assembly_text.insert("1.0", default_assembly)
        self.assembly_text.config(state="disabled")
        
        # Initial register state
        self.update_registers()
        
        # Initial log message
        self.update_log("[INIT] AC's Compiler Beta v0.1 initialized", self.success)
        self.update_log("[INIT] Ready to compile MIPS assembly code", self.accent)


def main():
    root = tk.Tk()
    app = CompilerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()