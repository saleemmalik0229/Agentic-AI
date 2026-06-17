import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.markdown import Markdown
from deep_research_backend.execution_engine import app as runner
from deep_research_backend.memory.history import get_history_manager

console = Console()
history_manager = get_history_manager()

async def main():
    console.print(Panel.fit("[bold blue]Deep Research Agent[/bold blue] - [italic]Terminal Interface[/italic]", border_style="blue"))
    console.print("[dim]Type 'exit' or 'quit' to stop.[/dim]\n")
    
    while True:
        try:
            query = console.input("[bold green]Enter your technical question:[/bold green] ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            # 1. Interactive Check
            # NOTE: history_manager is now async
            cached_answer = await history_manager.get(query)
            ignore_config = False
            
            if cached_answer:
                console.print("\n[bold yellow]ℹ You asked this question before.[/bold yellow]")
                choice = console.input("[bold cyan]Do you want to re-research this topic? [y/N]:[/bold cyan] ").strip().lower()
                
                if choice in ['y', 'yes']:
                    ignore_config = True
                    console.print("[dim]Forcing fresh research...[/dim]")
                else:
                    console.print("[dim]Fetching from memory...[/dim]")
                    console.print(Panel(Markdown(cached_answer), title="Cached Answer", border_style="yellow"))
                    console.print(f"\n[dim]{'-'*60}[/dim]\n")
                    continue

            inputs = {"user_query": query, "ignore_cache": ignore_config}
            
            # Using Rich Status for the "Brain" animation
            with console.status("[bold cyan]🧠 Reasoning...[/bold cyan]", spinner="dots") as status:
                async for event in runner.astream(inputs):
                    for key, value in event.items():
                        if key == "planner":
                            steps = len(value['plan'].steps)
                            console.print(f"[bold green]✓[/bold green] Plan generated with {steps} steps.")
                            status.update(f"[bold cyan]🧠 Executing Research Plan ({steps} steps)...[/bold cyan]")
                        elif key == "execute_step":
                             idx = value.get("current_step_index", 0)
                             console.print(f"  [dim]• Completed step {idx}[/dim]")
                        elif key == "synthesize":
                            status.update("[bold magenta]✨ Synthesizing final answer...[/bold magenta]")
                            console.print("\n[bold]Answer:[/bold]")
                            console.print(Panel(Markdown(value["final_answer"]), title="Agent Output", border_style="green"))
                            console.print(f"\n[dim]{'-'*60}[/dim]\n")

        except KeyboardInterrupt:
            console.print("\nExiting...")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
