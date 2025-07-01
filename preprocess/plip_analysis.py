#!/usr/bin/env python3  
"""  
PLIP相互作用分析脚本 - 返回原子对详细信息  
处理蛋白质口袋文件和小分子SDF文件  
"""  
  
import sys  
import os  
from plip.structure.preparation import PDBComplex  
  
def merge_protein_ligand_with_pymol(protein_file, ligand_file, output_file="complex.pdb"):  
    """使用PyMOL合并蛋白质和配体文件"""  
    try:  
        import pymol  
        from pymol import cmd  
          
        # 初始化PyMOL  
        pymol.finish_launching(['pymol', '-c'])  
        cmd.reinitialize()  
          
        print(f"使用PyMOL合并文件...")  
        print(f"  蛋白质文件: {protein_file}")  
        print(f"  配体文件: {ligand_file}")  
          
        # 加载蛋白质文件  
        cmd.load(protein_file, "protein")  
        print("  ✓ 蛋白质文件已加载")  
          
        # 加载配体文件  
        cmd.load(ligand_file, "ligand")  
        print("  ✓ 配体文件已加载")  
          
        # 创建复合物选择  
        cmd.create("complex", "protein or ligand")  
          
        # 保存复合物 - 使用绝对路径确保保存位置正确  
        abs_output_file = os.path.abspath(output_file)  
        cmd.save(abs_output_file, "complex")  
        print(f"  ✓ 复合物已保存为: {abs_output_file}")  
          
        # 强制刷新并等待文件写入完成  
        cmd.sync()  
          
        # 验证文件是否真的存在  
        if os.path.exists(abs_output_file):  
            print(f"  ✓ 文件验证成功: {abs_output_file}")  
            # file_size = os.path.getsize(abs_output_file)  
            # print(f"  ✓ 文件大小: {file_size} bytes")  
        else:  
            print(f"  ✗ 警告: 文件未找到: {abs_output_file}")  
            return False  
          
        # 清理PyMOL会话  
        cmd.reinitialize()  
          
        return True  
          
    except ImportError:  
        print("错误: 未找到PyMOL模块")  
        return False  
    except Exception as e:  
        print(f"PyMOL合并过程中出现错误: {e}")  
        return False  
          
    except ImportError:  
        print("错误: 未找到PyMOL模块")  
        print("请安装PyMOL: pip install pymol-open-source")  
        return False  
    except Exception as e:  
        print(f"PyMOL合并过程中出现错误: {e}")  
        return False  
  
def extract_interaction_atom_pairs(interaction_sets):  
    """  
    从interaction_sets中提取原子对的详细信息  
      
    Returns:  
        dict: 包含原子对信息的字典  
    """  
    atom_pairs_dict = {}  
      
    for bsid, interactions in interaction_sets.items():  
        atom_pairs_dict[bsid] = {  
            'hydrogen_bonds': [],  
            'hydrophobic_contacts': [],  
            'pi_stacking': [],  
            'pi_cation': [],  
            'salt_bridges': [],  
            'water_bridges': [],  
            'halogen_bonds': [],  
            'metal_complexes': []  
        }  
          
        # 氢键 - 基于plip/structure/detection.py中的hbonds函数  
        for hbond in interactions.hbonds_ldon + interactions.hbonds_pdon:  
            atom_pairs_dict[bsid]['hydrogen_bonds'].append({  
                'interaction_type': 'hydrogen_bond',  
                'protein_atom': {  
                    'residue_name': hbond.restype,  
                    'residue_number': hbond.resnr,  
                    'chain': hbond.reschain,  
                    'atom_type': hbond.dtype if hbond.protisdon else hbond.atype,  
                    'coordinates': hbond.d.coords if hbond.protisdon else hbond.a.coords  
                },  
                'ligand_atom': {  
                    'residue_name': hbond.restype_l,  
                    'residue_number': hbond.resnr_l,  
                    'chain': hbond.reschain_l,  
                    'atom_type': hbond.atype if hbond.protisdon else hbond.dtype,  
                    'coordinates': hbond.a.coords if hbond.protisdon else hbond.d.coords  
                },  
                'distance': hbond.distance_ad,  
                'angle': hbond.angle,  
                'protein_is_donor': hbond.protisdon,  
                'sidechain': hbond.sidechain  
            })  
          
        # 疏水相互作用 - 基于plip/structure/detection.py中的hydrophobic_interactions函数  
        for hydrophobic in interactions.hydrophobic_contacts:  
            atom_pairs_dict[bsid]['hydrophobic_contacts'].append({  
                'interaction_type': 'hydrophobic_contact',  
                'protein_atom': {  
                    'residue_name': hydrophobic.restype,  
                    'residue_number': hydrophobic.resnr,  
                    'chain': hydrophobic.reschain,  
                    'atom_type': 'C',  # 疏水相互作用主要是碳原子  
                    'coordinates': hydrophobic.bsatom.coords  
                },  
                'ligand_atom': {  
                    'residue_name': hydrophobic.restype_l,  
                    'residue_number': hydrophobic.resnr_l,  
                    'chain': hydrophobic.reschain_l,  
                    'atom_type': 'C',  
                    'coordinates': hydrophobic.ligatom.coords  
                },  
                'distance': hydrophobic.distance  
            })  
          
        # π-π堆积  
        for pistack in interactions.pistacking:  
            # 获取环原子信息  
            protein_ring_atoms = []  
            ligand_ring_atoms = []  
              
            for atom in pistack.proteinring.atoms:  
                protein_ring_atoms.append({  
                    'atom_type': atom.type,  
                    'coordinates': atom.coords  
                })  
              
            for atom in pistack.ligandring.atoms:  
                ligand_ring_atoms.append({  
                    'atom_type': atom.type,  
                    'coordinates': atom.coords  
                })  
              
            atom_pairs_dict[bsid]['pi_stacking'].append({  
                'interaction_type': 'pi_stacking',  
                'protein_ring': {  
                    'residue_name': pistack.restype,  
                    'residue_number': pistack.resnr,  
                    'chain': pistack.reschain,  
                    'ring_center': pistack.proteinring.center,  
                    'atoms': protein_ring_atoms  
                },  
                'ligand_ring': {  
                    'residue_name': pistack.restype_l,  
                    'residue_number': pistack.resnr_l,  
                    'chain': pistack.reschain_l,  
                    'ring_center': pistack.ligandring.center,  
                    'atoms': ligand_ring_atoms  
                },  
                'distance': pistack.distance,  
                'angle': pistack.angle,  
                'offset': pistack.offset,  
                'type': pistack.type  
            })  
          
        # π-阳离子相互作用  
        for pication in interactions.pication_laro + interactions.pication_paro:  
            atom_pairs_dict[bsid]['pi_cation'].append({  
                'interaction_type': 'pi_cation',  
                'ring_info': {  
                    'center': pication.ring.center,  
                    'atoms': [{'atom_type': atom.type, 'coordinates': atom.coords}   
                             for atom in pication.ring.atoms]  
                },  
                'charge_info': {  
                    'center': pication.charge.center,  
                    'atoms': [{'atom_type': atom.type, 'coordinates': atom.coords}   
                             for atom in pication.charge.atoms]  
                },  
                'protein_residue': {  
                    'residue_name': pication.restype,  
                    'residue_number': pication.resnr,  
                    'chain': pication.reschain  
                },  
                'ligand_residue': {  
                    'residue_name': pication.restype_l,  
                    'residue_number': pication.resnr_l,  
                    'chain': pication.reschain_l  
                },  
                'distance': pication.distance,  
                'offset': pication.offset,  
                'protein_charged': pication.protcharged  
            })  
          
        # 盐桥  
        for saltbridge in interactions.saltbridge_lneg + interactions.saltbridge_pneg:  
            atom_pairs_dict[bsid]['salt_bridges'].append({  
                'interaction_type': 'salt_bridge',  
                'positive_charge': {  
                    'center': saltbridge.positive.center,  
                    'atoms': [{'atom_type': atom.type, 'coordinates': atom.coords}   
                             for atom in saltbridge.positive.atoms]  
                },  
                'negative_charge': {  
                    'center': saltbridge.negative.center,  
                    'atoms': [{'atom_type': atom.type, 'coordinates': atom.coords}   
                             for atom in saltbridge.negative.atoms]  
                },  
                'protein_residue': {  
                    'residue_name': saltbridge.restype,  
                    'residue_number': saltbridge.resnr,  
                    'chain': saltbridge.reschain  
                },  
                'ligand_residue': {  
                    'residue_name': saltbridge.restype_l,  
                    'residue_number': saltbridge.resnr_l,  
                    'chain': saltbridge.reschain_l  
                },  
                'distance': saltbridge.distance,  
                'protein_is_positive': saltbridge.protispos  
            })  
          
        # 水桥  
        for wbridge in interactions.water_bridges:  
            atom_pairs_dict[bsid]['water_bridges'].append({  
                'interaction_type': 'water_bridge',  
                'protein_atom': {  
                    'residue_name': wbridge.restype,  
                    'residue_number': wbridge.resnr,  
                    'chain': wbridge.reschain,  
                    'atom_type': wbridge.dtype if wbridge.protisdon else wbridge.atype,  
                    'coordinates': wbridge.d.coords if wbridge.protisdon else wbridge.a.coords  
                },  
                'ligand_atom': {  
                    'residue_name': wbridge.restype_l,  
                    'residue_number': wbridge.resnr_l,  
                    'chain': wbridge.reschain_l,  
                    'atom_type': wbridge.atype if wbridge.protisdon else wbridge.dtype,  
                    'coordinates': wbridge.a.coords if wbridge.protisdon else wbridge.d.coords  
                },  
                'water_atom': {  
                    'coordinates': wbridge.water.coords  
                },  
                'distance_donor_water': wbridge.distance_dw,  
                'distance_acceptor_water': wbridge.distance_aw,  
                'donor_angle': wbridge.angle_don,  
                'water_angle': wbridge.angle_water,  
                'protein_is_donor': wbridge.protisdon  
            })  
          
        # 卤键  
        for halogen in interactions.halogen_bonds:  
            atom_pairs_dict[bsid]['halogen_bonds'].append({  
                'interaction_type': 'halogen_bond',  
                'donor_atom': {  
                    'residue_name': halogen.restype_l,  
                    'residue_number': halogen.resnr_l,  
                    'chain': halogen.reschain_l,  
                    'atom_type': halogen.donortype,  
                    'coordinates': halogen.don.coords  
                },  
                'acceptor_atom': {  
                    'residue_name': halogen.restype,  
                    'residue_number': halogen.resnr,  
                    'chain': halogen.reschain,  
                    'atom_type': halogen.acctype,  
                    'coordinates': halogen.acc.coords  
                },  
                'distance': halogen.distance,  
                'donor_angle': halogen.don_angle,  
                'acceptor_angle': halogen.acc_angle,  
                'sidechain': halogen.sidechain  
            })  
          
        # 金属配位  
        for metal in interactions.metal_complexes:  
            atom_pairs_dict[bsid]['metal_complexes'].append({  
                'interaction_type': 'metal_complex',  
                'metal_atom': {  
                    'atom_type': metal.metal_type,  
                    'coordinates': metal.metal.coords  
                },  
                'target_atom': {  
                    'residue_name': metal.restype,  
                    'residue_number': metal.resnr,  
                    'chain': metal.reschain,  
                    'atom_type': metal.target_type,  
                    'coordinates': metal.target.atom.coords  
                },  
                'distance': metal.distance,  
                'coordination_number': metal.coordination_num,  
                'geometry': metal.geometry,  
                'location': metal.location,  
                'rms': metal.rms  
            })  
      
    return atom_pairs_dict  
  
def analyze_protein_ligand_interactions(protein_file, ligand_sdf_file):  
    """分析蛋白质-配体相互作用并返回详细的原子对信息"""  
      
    if not os.path.exists(protein_file):  
        raise FileNotFoundError(f"蛋白质文件不存在: {protein_file}")  
    if not os.path.exists(ligand_sdf_file):  
        raise FileNotFoundError(f"配体文件不存在: {ligand_sdf_file}")  
      
    complex_file = "complex.pdb"  
      
    if os.path.exists(complex_file):  
        print(f"发现已存在的复合物文件: {complex_file}")  
        use_existing = input("是否使用现有文件？(y/n): ").lower().strip()  
        if use_existing != 'y':  
            print("重新生成复合物文件...")  
            if not merge_protein_ligand_with_pymol(protein_file, ligand_sdf_file, complex_file):  
                return {}  
    else:  
        print("未找到复合物文件，使用PyMOL自动生成...")  
        if not merge_protein_ligand_with_pymol(protein_file, ligand_sdf_file, complex_file):  
            return {}  
      
    try:  
        # 创建PDBComplex实例并分析  
        my_mol = PDBComplex()  
        my_mol.load_pdb(complex_file)  
          
        print(f"\n加载的结构: {my_mol}")  
        print(f"发现的配体数量: {len(my_mol.ligands)}")  
          
        if len(my_mol.ligands) == 0:  
            print("错误: 在复合物文件中未发现配体")  
            return {}  
          
        print("开始分析相互作用...")  
        my_mol.analyze()  
          
        # 提取详细的原子对信息  
        atom_pairs_dict = extract_interaction_atom_pairs(my_mol.interaction_sets)  
          
        return atom_pairs_dict  
          
    except Exception as e:  
        print(f"分析过程中出现错误: {e}")  