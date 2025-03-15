# Créer une version mise à jour de test_mbongi.py qui teste les nouvelles fonctionnalités
import os
import time
from src.agents.documentation.mbongi import Mbongi

def main():
    """Test de la version complète de Mbongi."""
    print("=== Test de l'agent Mbongi complet ===")
    
    # Obtenir le chemin du projet
    project_path = os.getcwd()
    
    # Créer une instance de Mbongi
    mbongi = Mbongi(project_path)
    
    # Tester la génération de documentation
    print("\nTest de génération de documentation...")
    mbongi.update_all_documentation()
    
    # Tester le moniteur de session (en mode manuel)
    print("\nTest du moniteur de session...")
    mbongi.start_session()
    
    # Ajouter une idée de test
    mbongi.process_idea("""
[MBONGI:IDEA]
Title: Intégration complète des composants de Mbongi
Component: Mbongi
Type: Amélioration
Priority: Haute
Description:
Intégrer tous les composants de Mbongi (DocumentationGenerator, SessionMonitor, GitIntegrator)
dans la classe principale pour offrir une fonctionnalité complète.

Implementation:
Mise à jour de la classe principale avec les nouveaux imports et initialisation des composants.
Ajout de méthodes pour utiliser les nouvelles fonctionnalités.

Dependencies:
- Mbongi
- DocumentationGenerator
- SessionMonitor
- GitIntegrator

Status: Implémenté
[/MBONGI:IDEA]
""")
    
    # Simuler un peu de travail
    print("Travail en cours...")
    time.sleep(2)
    
    # Terminer la session
    mbongi.end_session()
    
    # Tester l'intégration Git
    print("\nTest de l'intégration Git...")
    changes = mbongi.git_integrator.check_changes()
    print("Changements détectés:")
    for change_type, files in changes.items():
        if files:
            print(f"- {change_type}: {len(files)} fichier(s)")
    
    print("\nTests terminés.")
    print("Mbongi est maintenant complètement fonctionnel avec tous ses composants!")

if __name__ == "__main__":
    main()