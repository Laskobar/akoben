"""
Module d'analyse de code pour Mbongi.
Adapté du projet Eliza pour Akoben.
Analyse le code source Python pour extraire des informations structurées.
"""

import os
import ast
import inspect
import importlib.util
import re
from typing import Dict, List, Any, Optional, Tuple, Set, Union


class CodeAnalyzer:
    """
    Analyseur de code pour extraire des informations structurées du code source Python.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialise l'analyseur de code.
        
        Args:
            config: Dictionnaire de configuration optionnel
        """
        self.config = config or {}
        self.project_base_path = self.config.get('project_base_path', os.getcwd())
        
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyse un fichier Python et extrait ses informations structurées.
        
        Args:
            file_path: Chemin du fichier à analyser
            
        Returns:
            Dictionnaire contenant les informations extraites
        """
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        
        # Vérifier que c'est un fichier Python
        if not file_path.endswith('.py'):
            raise ValueError(f"Le fichier {file_path} n'est pas un fichier Python (.py)")
        
        # Lire le fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Extraire les informations de base
        result = {
            'file_path': file_path,
            'relative_path': os.path.relpath(file_path, self.project_base_path),
            'filename': os.path.basename(file_path),
            'size': len(source_code),
            'line_count': len(source_code.split('\n')),
        }
        
        # Essayer de parser le code avec ast
        try:
            tree = ast.parse(source_code)
            
            # Extraire les docstrings et autres métadonnées
            result['module_docstring'] = ast.get_docstring(tree)
            result['imports'] = self._extract_imports(tree)
            result['classes'] = self._extract_classes(tree, source_code)
            result['functions'] = self._extract_functions(tree, source_code)
            result['global_variables'] = self._extract_global_variables(tree)
            
            # Analyse supplémentaire
            result['metrics'] = self._calculate_metrics(tree, source_code)
            result['dependencies'] = self._analyze_dependencies(result['imports'])
            
        except SyntaxError as e:
            result['error'] = f"Erreur de syntaxe: {str(e)}"
            result['classes'] = []
            result['functions'] = []
            result['imports'] = []
            result['global_variables'] = []
            result['metrics'] = {}
            result['dependencies'] = []
        
        return result
    
    def _extract_imports(self, tree: ast.Module) -> List[Dict[str, str]]:
        """Extrait les imports du code."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append({
                        'type': 'import',
                        'name': name.name,
                        'alias': name.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for name in node.names:
                    imports.append({
                        'type': 'from',
                        'module': module,
                        'name': name.name,
                        'alias': name.asname
                    })
        return imports
    
    def _extract_classes(self, tree: ast.Module, source_code: str) -> List[Dict[str, Any]]:
        """Extrait les classes et leurs méthodes."""
        classes = []
        for node in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            methods = []
            class_attrs = []
            
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(self._extract_function_data(item, source_code))
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_attrs.append({
                                'name': target.id,
                                'lineno': item.lineno
                            })
            
            classes.append({
                'name': node.name,
                'lineno': node.lineno,
                'docstring': ast.get_docstring(node),
                'methods': methods,
                'attributes': class_attrs,
                'bases': [self._get_base_name(base) for base in node.bases],
                'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
            })
        return classes
    
    def _extract_functions(self, tree: ast.Module, source_code: str) -> List[Dict[str, Any]]:
        """Extrait les fonctions au niveau du module."""
        return [
            self._extract_function_data(node, source_code)
            for node in tree.body if isinstance(node, ast.FunctionDef)
        ]
    
    def _extract_function_data(self, node: ast.FunctionDef, source_code: str) -> Dict[str, Any]:
        """Extrait les données d'une fonction ou méthode."""
        # Extraire la signature de la fonction
        args = []
        defaults = {}
        
        # Arguments positionnels
        for i, arg in enumerate(node.args.args):
            arg_name = arg.arg
            args.append(arg_name)
            
            # Si cet argument a une valeur par défaut
            default_index = i - len(node.args.args) + len(node.args.defaults)
            if default_index >= 0:
                defaults[arg_name] = self._get_default_value(node.args.defaults[default_index])
        
        # Arguments keyword-only
        for i, arg in enumerate(node.args.kwonlyargs):
            arg_name = arg.arg
            args.append(arg_name)
            
            # Si cet argument a une valeur par défaut
            if i < len(node.args.kw_defaults) and node.args.kw_defaults[i] is not None:
                defaults[arg_name] = self._get_default_value(node.args.kw_defaults[i])
        
        # Extraire le type de retour s'il est spécifié
        returns = None
        if node.returns:
            returns = self._get_annotation(node.returns)
        
        # Récupérer le code source de la fonction
        try:
            func_source = self._get_source_segment(source_code, node)
        except:
            func_source = "Source non disponible"
        
        return {
            'name': node.name,
            'lineno': node.lineno,
            'docstring': ast.get_docstring(node),
            'args': args,
            'defaults': defaults,
            'returns': returns,
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
            'source': func_source
        }
    
    def _extract_global_variables(self, tree: ast.Module) -> List[Dict[str, Any]]:
        """Extrait les variables globales du module."""
        global_vars = []
        for node in [n for n in tree.body if isinstance(n, ast.Assign)]:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    value = "Complex value"
                    if isinstance(node.value, (ast.Str, ast.Num, ast.NameConstant)):
                        value = ast.literal_eval(node.value)
                    elif isinstance(node.value, ast.Name):
                        value = f"Reference to {node.value.id}"
                    
                    global_vars.append({
                        'name': target.id,
                        'value': value,
                        'lineno': node.lineno
                    })
        return global_vars
    
    def _calculate_metrics(self, tree: ast.Module, source_code: str) -> Dict[str, Any]:
        """Calcule diverses métriques de code."""
        metrics = {
            'class_count': len([n for n in tree.body if isinstance(n, ast.ClassDef)]),
            'function_count': len([n for n in tree.body if isinstance(n, ast.FunctionDef)]),
            'import_count': len([n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]),
            'comment_lines': self._count_comment_lines(source_code),
            'complexity': self._calculate_complexity(tree)
        }
        
        # Calcul de la densité de documentation
        total_lines = metrics['class_count'] + metrics['function_count']
        doc_lines = sum(1 for node in ast.walk(tree) 
                       if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and ast.get_docstring(node))
        
        metrics['documentation_ratio'] = doc_lines / total_lines if total_lines > 0 else 0
        
        return metrics
    
    def _count_comment_lines(self, source_code: str) -> int:
        """Compte le nombre de lignes de commentaires."""
        comment_count = 0
        for line in source_code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('#'):
                comment_count += 1
        return comment_count
    
    def _calculate_complexity(self, tree: ast.Module) -> Dict[str, Any]:
        """Calcule une estimation simple de la complexité cyclomatique."""
        complexity = {'total': 0, 'per_function': {}}
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Initialiser la complexité à 1 pour le point d'entrée
                func_complexity = 1
                
                # Parcourir le corps de la fonction
                for inner_node in ast.walk(node):
                    # Incrémenter pour chaque structure de contrôle
                    if isinstance(inner_node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                        func_complexity += 1
                    elif isinstance(inner_node, ast.BoolOp) and isinstance(inner_node.op, ast.And):
                        func_complexity += len(inner_node.values) - 1
                
                complexity['per_function'][node.name] = func_complexity
                complexity['total'] += func_complexity
        
        return complexity
    
    def _analyze_dependencies(self, imports: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Analyse les dépendances extraites des imports."""
        dependencies = []
        
        for imp in imports:
            dep_type = None
            name = imp.get('name', '')
            module = imp.get('module', '')
            
            # Déterminer le type de dépendance
            full_name = f"{module}.{name}" if module else name
            
            if full_name.startswith('src.agents'):
                dep_type = 'internal_agent'
            elif full_name.startswith('src.anansi'):
                dep_type = 'internal_anansi'
            elif full_name.startswith('src.'):
                dep_type = 'internal_other'
            elif full_name in ['os', 'sys', 're', 'json', 'datetime', 'collections', 'typing']:
                dep_type = 'stdlib'
            else:
                dep_type = 'external'
            
            dependencies.append({
                'name': full_name,
                'type': dep_type
            })
        
        return dependencies
    
    def analyze_directory(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Analyse un répertoire de fichiers Python.
        
        Args:
            directory_path: Chemin du répertoire à analyser
            recursive: Analyser récursivement les sous-répertoires
            
        Returns:
            Dictionnaire avec les résultats d'analyse
        """
        if not os.path.isdir(directory_path):
            raise NotADirectoryError(f"{directory_path} n'est pas un répertoire")
        
        results = {
            'directory': directory_path,
            'files': [],
            'summary': {
                'file_count': 0,
                'total_lines': 0,
                'class_count': 0,
                'function_count': 0,
                'average_complexity': 0
            }
        }
        
        total_complexity = 0
        
        # Parcourir les fichiers
        for root, dirs, files in os.walk(directory_path):
            if not recursive and root != directory_path:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        file_analysis = self.analyze_file(file_path)
                        results['files'].append(file_analysis)
                        
                        # Mettre à jour les statistiques de synthèse
                        results['summary']['file_count'] += 1
                        results['summary']['total_lines'] += file_analysis['line_count']
                        results['summary']['class_count'] += file_analysis['metrics']['class_count']
                        results['summary']['function_count'] += file_analysis['metrics']['function_count']
                        total_complexity += file_analysis['metrics']['complexity']['total']
                    except Exception as e:
                        print(f"Erreur lors de l'analyse de {file_path}: {str(e)}")
        
        # Calculer la complexité moyenne
        if results['summary']['function_count'] > 0:
            results['summary']['average_complexity'] = total_complexity / results['summary']['function_count']
        
        return results
    
    def detect_dependencies(self, file_path: str) -> Dict[str, Set[str]]:
        """
        Détecte les dépendances entre un fichier et les autres composants du projet.
        
        Args:
            file_path: Chemin du fichier à analyser
            
        Returns:
            Dictionnaire des dépendances par type
        """
        analysis = self.analyze_file(file_path)
        
        dependencies = {
            'internal_agents': set(),
            'internal_anansi': set(),
            'internal_other': set(),
            'external': set(),
            'stdlib': set()
        }
        
        for dep in analysis['dependencies']:
            dep_name = dep['name']
            dep_type = dep['type']
            
            if dep_type == 'internal_agent':
                dependencies['internal_agents'].add(dep_name)
            elif dep_type == 'internal_anansi':
                dependencies['internal_anansi'].add(dep_name)
            elif dep_type == 'internal_other':
                dependencies['internal_other'].add(dep_name)
            elif dep_type == 'stdlib':
                dependencies['stdlib'].add(dep_name)
            else:
                dependencies['external'].add(dep_name)
        
        return dependencies
    
    # Méthodes utilitaires
    def _get_base_name(self, node: ast.expr) -> str:
        """Extrait le nom d'une classe de base."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        else:
            return str(node)
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Extrait le nom d'un décorateur."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        else:
            return str(node)
    
    def _get_default_value(self, node: ast.expr) -> Any:
        """Extrait la valeur par défaut d'un argument."""
        if isinstance(node, (ast.Str, ast.Num, ast.NameConstant)):
            return ast.literal_eval(node)
        elif isinstance(node, ast.Name):
            return f"Reference to {node.id}"
        elif isinstance(node, ast.Dict):
            return "Dict"
        elif isinstance(node, ast.List):
            return "List"
        elif isinstance(node, ast.Tuple):
            return "Tuple"
        elif isinstance(node, ast.Set):
            return "Set"
        else:
            return "Complex default value"
    
    def _get_annotation(self, node: ast.expr) -> str:
        """Extrait le type annoté."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_annotation(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_annotation(node.value)}[...]"
        else:
            return "Complex type"
    
    def _get_source_segment(self, source: str, node: ast.AST) -> str:
        """Récupère le segment de code source correspondant à un nœud AST."""
        lines = source.splitlines()
        
        # Trouver la fin du nœud (approximative)
        end_lineno = 0
        for descendant in ast.walk(node):
            if hasattr(descendant, 'lineno'):
                end_lineno = max(end_lineno, descendant.lineno)
        
        # Extraire les lignes
        start = node.lineno - 1
        end = min(end_lineno, len(lines))
        return '\n'.join(lines[start:end])


# Test simple du module si exécuté directement
if __name__ == "__main__":
    analyzer = CodeAnalyzer()
    
    # Analyser le propre fichier du module
    current_file = __file__
    print(f"Analyse de {current_file}...")
    
    try:
        result = analyzer.analyze_file(current_file)
        
        print(f"Nombre de lignes: {result['line_count']}")
        print(f"Nombre de classes: {result['metrics']['class_count']}")
        print(f"Nombre de fonctions: {result['metrics']['function_count']}")
        print(f"Complexité totale: {result['metrics']['complexity']['total']}")
        
        if result['classes']:
            print("\nClasses:")
            for cls in result['classes']:
                print(f"  - {cls['name']} ({len(cls['methods'])} méthodes)")
        
        if result['imports']:
            print("\nImports:")
            for imp in result['imports']:
                if imp['type'] == 'import':
                    print(f"  - import {imp['name']}")
                else:
                    print(f"  - from {imp['module']} import {imp['name']}")
        
    except Exception as e:
        print(f"Erreur: {str(e)}")