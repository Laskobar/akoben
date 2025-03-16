# À ajouter à src/anansi/core.py ou dans un nouveau fichier src/anansi/agent_manager.py

class AgentManager:
    """
    Gestionnaire d'agents pour Anansi, responsable de la création,
    du suivi et de l'orchestration des agents autonomes.
    """
    
    def __init__(self, anansi_core):
        self.anansi_core = anansi_core
        self.agents = {}
        self.agent_teams = {}
        self.workflows = {}
        self.logger = logging.getLogger("akoben.anansi.agent_manager")
        
    def register_agent(self, agent_instance):
        """
        Enregistre un agent dans le système.
        """
        if agent_instance.name in self.agents:
            self.logger.warning(f"Agent {agent_instance.name} déjà enregistré, mise à jour")
            
        self.agents[agent_instance.name] = agent_instance
        self.logger.info(f"Agent {agent_instance.name} enregistré avec succès")
        return True
        
    def create_agent(self, agent_class, name, config=None):
        """
        Crée et enregistre un nouvel agent à partir de sa classe.
        """
        if name in self.agents:
            self.logger.warning(f"Un agent nommé {name} existe déjà")
            return None
            
        try:
            agent_instance = agent_class(name=name, config=config, anansi_core=self.anansi_core)
            self.register_agent(agent_instance)
            return agent_instance
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'agent {name}: {str(e)}")
            return None
            
    def create_team(self, team_name, agent_names=None):
        """
        Crée une équipe d'agents qui travailleront ensemble.
        """
        if team_name in self.agent_teams:
            self.logger.warning(f"Une équipe nommée {team_name} existe déjà")
            return False
            
        self.agent_teams[team_name] = {
            "name": team_name,
            "agents": agent_names or [],
            "created_at": time.time()
        }
        
        self.logger.info(f"Équipe {team_name} créée avec les agents: {agent_names}")
        return True
        
    def add_agent_to_team(self, agent_name, team_name):
        """
        Ajoute un agent à une équipe existante.
        """
        if team_name not in self.agent_teams:
            self.logger.error(f"L'équipe {team_name} n'existe pas")
            return False
            
        if agent_name not in self.agents:
            self.logger.error(f"L'agent {agent_name} n'existe pas")
            return False
            
        if agent_name in self.agent_teams[team_name]["agents"]:
            self.logger.warning(f"L'agent {agent_name} est déjà dans l'équipe {team_name}")
            return True
            
        self.agent_teams[team_name]["agents"].append(agent_name)
        self.logger.info(f"Agent {agent_name} ajouté à l'équipe {team_name}")
        return True
        
    def define_workflow(self, workflow_name, steps):
        """
        Définit un workflow comme une séquence d'étapes d'agents.
        
        Args:
            workflow_name: Nom unique du workflow
            steps: Liste de dictionnaires décrivant les étapes du workflow
                  [{"agent": "nom_agent", "action": "nom_action", "params": {}}, ...]
        """
        if workflow_name in self.workflows:
            self.logger.warning(f"Un workflow nommé {workflow_name} existe déjà, écrasement")
            
        # Validation des agents dans les étapes
        for i, step in enumerate(steps):
            agent_name = step.get("agent")
            if agent_name not in self.agents:
                self.logger.error(f"Étape {i}: l'agent {agent_name} n'existe pas")
                return False
                
        self.workflows[workflow_name] = {
            "name": workflow_name,
            "steps": steps,
            "created_at": time.time(),
            "last_run": None
        }
        
        self.logger.info(f"Workflow {workflow_name} défini avec {len(steps)} étapes")
        return True
        
    def execute_workflow(self, workflow_name, initial_input=None):
        """
        Exécute un workflow complet, en passant les résultats d'une étape à l'autre.
        """
        if workflow_name not in self.workflows:
            self.logger.error(f"Le workflow {workflow_name} n'existe pas")
            return None
            
        workflow = self.workflows[workflow_name]
        current_input = initial_input
        results = []
        
        self.logger.info(f"Exécution du workflow {workflow_name}")
        
        for i, step in enumerate(workflow["steps"]):
            agent_name = step["agent"]
            action = step["action"]
            params = step.get("params", {})
            
            agent = self.agents[agent_name]
            self.logger.info(f"Étape {i+1}: Agent {agent_name}, Action {action}")
            
            try:
                # Exécution de l'action spécifiée sur l'agent
                if action == "cognitive_cycle":
                    result = agent.cognitive_cycle(current_input, params)
                elif hasattr(agent, action) and callable(getattr(agent, action)):
                    method = getattr(agent, action)
                    result = method(current_input, **params)
                else:
                    self.logger.error(f"Action {action} non disponible pour l'agent {agent_name}")
                    return None
                    
                results.append({
                    "step": i,
                    "agent": agent_name,
                    "action": action,
                    "result": result
                })
                
                # L'output d'une étape devient l'input de la suivante
                current_input = result
                
            except Exception as e:
                self.logger.error(f"Erreur lors de l'étape {i+1}: {str(e)}")
                results.append({
                    "step": i,
                    "agent": agent_name,
                    "action": action,
                    "error": str(e)
                })
                return results
                
        # Mise à jour du timestamp de dernière exécution
        self.workflows[workflow_name]["last_run"] = time.time()
        
        return results