import tensorflow as tf
import numpy as np
import os
import json
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# state_size, action_size, upper_bound, stock_list, maxlen

class TradeModel(object):
    def __init__(self, model_path="model"):
        self.param_path = os.path.join(model_path, "parameters")
        self.model_path = os.path.join(model_path, "model_weights")
        self.model_config_path = os.path.join(model_path, "model_config")
        self.actor, self.critic = self.get_models()
        self.load_weights()

    def get_models(self):
        actor_file_path = "model/model_config/actor.json"
        critic_file_path = "model/model_config/critic.json"
        with open(actor_file_path, 'r') as f:
            actor_config = json.load(f)
        with open(actor_file_path, 'r') as f:
            critic_config = json.load(f)
        actor = tf.keras.models.model_from_config(actor_config)
        critic = tf.keras.models.model_from_config(critic_config)

        return actor, critic

    def load_weights(self):
        self.actor.load_weights(f"model/model_weights/actor")
        self.critic.load_weights(f"model/model_weights/critic")


    @tf.function
    def get_policy(self, state, get_critic_value=True):
        state = tf.expand_dims(state, 0)
        actions = tf.squeeze(self.actor(state))

        if get_critic_value:
            q_value = tf.squeeze(self.critic([state, tf.expand_dims(actions, 0)]))
            return actions, q_value

        return actions

    def get_action(self, state):
        state = tf.convert_to_tensor(state)
        actions, q_value = self.get_policy(state, get_critic_value=True)
        actions = actions.numpy()
        q_value = q_value.numpy()
        actions = np.round(np.clip(actions, -self.upper_bound, self.upper_bound))
        actions = np.squeeze(actions)
        return actions
